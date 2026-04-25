import { useMemo, memo } from 'react'
import { MeshStandardMaterial, CanvasTexture, Shape, ExtrudeGeometry } from 'three'

interface Hexagram3DProps {
  bits: string
  isLoading?: boolean
}

const TOTAL_WIDTH = 2.4
const YIN_GAP = 0.5
const GAP_Y = 0.85
const Y_OFFSET = ((6 - 1) * GAP_Y) / 2
const YIN_SEGMENT_LENGTH = (TOTAL_WIDTH - YIN_GAP) / 2
const YIN_OFFSET_X = (YIN_GAP / 2) + (YIN_SEGMENT_LENGTH / 2)

// =============================================================================
// Procedural Ink Texture (Canvas-generated)
// =============================================================================

function createInkTexture(dark: boolean): CanvasTexture {
  const canvas = document.createElement('canvas')
  canvas.width = 256
  canvas.height = 256
  const ctx = canvas.getContext('2d')!

  // 宣纸底色
  ctx.fillStyle = dark ? '#f4f4f0' : '#d0d0c8'
  ctx.fillRect(0, 0, 256, 256)

  // 墨迹核心：浓淡不均的椭圆形
  const gradient = ctx.createRadialGradient(128, 128, 0, 128, 128, 120)
  if (dark) {
    gradient.addColorStop(0, 'rgba(20, 20, 20, 0.92)')
    gradient.addColorStop(0.35, 'rgba(15, 15, 15, 0.75)')
    gradient.addColorStop(0.65, 'rgba(8, 8, 8, 0.4)')
    gradient.addColorStop(1, 'rgba(3, 3, 3, 0)')
  } else {
    gradient.addColorStop(0, 'rgba(80, 78, 75, 0.7)')
    gradient.addColorStop(0.35, 'rgba(60, 58, 55, 0.5)')
    gradient.addColorStop(0.65, 'rgba(40, 38, 35, 0.25)')
    gradient.addColorStop(1, 'rgba(20, 18, 15, 0)')
  }

  ctx.fillStyle = gradient
  ctx.beginPath()
  ctx.ellipse(128, 128, 105, 48, 0, 0, Math.PI * 2)
  ctx.fill()

  // 飞白纹理
  ctx.globalCompositeOperation = 'destination-out'
  for (let i = 0; i < 120; i++) {
    const x = Math.random() * 256
    const y = Math.random() * 256
    const r = Math.random() * 4 + 0.5
    const alpha = Math.random() * 0.35
    ctx.fillStyle = `rgba(255,255,255,${alpha})`
    ctx.beginPath()
    ctx.arc(x, y, r, 0, Math.PI * 2)
    ctx.fill()
  }

  // 墨点细节
  for (let i = 0; i < 30; i++) {
    const x = Math.random() * 256
    const y = Math.random() * 256
    ctx.fillStyle = 'rgba(255,255,255,0.05)'
    ctx.beginPath()
    ctx.ellipse(x, y, Math.random() * 10 + 2, Math.random() * 3 + 1, Math.random() * Math.PI, 0, Math.PI * 2)
    ctx.fill()
  }

  const texture = new CanvasTexture(canvas)
  texture.needsUpdate = true
  return texture
}

// =============================================================================
// Materials
// =============================================================================

function useInkMaterial(tone: 'dark' | 'light') {
  return useMemo(() => {
    const texture = createInkTexture(tone === 'dark')

    const mat = new MeshStandardMaterial({
      color: tone === 'dark' ? '#111111' : '#3a3a3a',
      roughness: 0.9,
      metalness: 0.0,
      transparent: true,
      opacity: 0.92,
    })

    mat.map = texture
    mat.alphaMap = texture
    mat.transparent = true
    mat.depthWrite = false

    return mat
  }, [tone])
}

// =============================================================================
// Yang: 毛笔实笔 — custom brush stroke shape
// =============================================================================

function createBrushStrokeShape(): Shape {
  const shape = new Shape()

  const hw = TOTAL_WIDTH / 2
  const th = 0.12

  shape.moveTo(-hw, -th * 0.3)
  shape.quadraticCurveTo(-hw + 0.05, -th * 0.8, -hw + 0.15, -th)
  shape.quadraticCurveTo(-hw * 0.3, -th * 1.1, 0, -th * 1.05)
  shape.quadraticCurveTo(hw * 0.3, -th * 1.0, hw - 0.15, -th * 0.9)
  shape.quadraticCurveTo(hw - 0.05, -th * 0.6, hw, -th * 0.2)

  shape.lineTo(hw, th * 0.2)
  shape.quadraticCurveTo(hw - 0.05, th * 0.6, hw - 0.15, th * 0.9)
  shape.quadraticCurveTo(hw * 0.3, th * 1.0, 0, th * 1.05)
  shape.quadraticCurveTo(-hw * 0.3, th * 1.1, -hw + 0.15, th)
  shape.quadraticCurveTo(-hw + 0.05, th * 0.8, -hw, th * 0.3)

  shape.closePath()
  return shape
}

function Yang({ index }: { index: number }) {
  const y = index * GAP_Y - Y_OFFSET
  const material = useInkMaterial('dark')

  const geometry = useMemo(() => {
    const shape = createBrushStrokeShape()
    return new ExtrudeGeometry(shape, {
      depth: 0.16,
      bevelEnabled: true,
      bevelThickness: 0.03,
      bevelSize: 0.03,
      bevelSegments: 3,
    })
  }, [])

  return (
    <mesh position={[0, y, 0]} rotation={[0, 0, 0]} scale={[1, 1, 0.2]} material={material} geometry={geometry} />
  )
}

// =============================================================================
// Yin: 毛笔断笔 — 两段断开，边缘飞白
// =============================================================================

function createYinSegmentShape(startTaper: number, endTaper: number): Shape {
  const shape = new Shape()
  const len = YIN_SEGMENT_LENGTH * 0.88
  const hw = len / 2
  const th = 0.1

  shape.moveTo(-hw, -th * startTaper)
  shape.quadraticCurveTo(-hw + 0.08, -th * startTaper * 1.2, -hw + 0.18, -th)
  shape.quadraticCurveTo(-hw * 0.3, -th * 1.05, 0, -th * 1.02)
  shape.quadraticCurveTo(hw * 0.3, -th * 1.0, hw - 0.18, -th * endTaper)
  shape.quadraticCurveTo(hw - 0.08, -th * endTaper * 0.8, hw, -th * endTaper * 0.3)

  shape.lineTo(hw, th * endTaper * 0.3)
  shape.quadraticCurveTo(hw - 0.08, th * endTaper * 0.8, hw - 0.18, th * endTaper)
  shape.quadraticCurveTo(hw * 0.3, th * 1.0, 0, th * 1.02)
  shape.quadraticCurveTo(-hw * 0.3, th * 1.05, -hw + 0.18, th)
  shape.quadraticCurveTo(-hw + 0.08, th * startTaper * 1.2, -hw, th * startTaper * 0.3)

  shape.closePath()
  return shape
}

function Yin({ index }: { index: number }) {
  const y = index * GAP_Y - Y_OFFSET
  const material = useInkMaterial('light')

  const leftGeom = useMemo(() => {
    return new ExtrudeGeometry(createYinSegmentShape(0.5, 1.0), {
      depth: 0.14,
      bevelEnabled: true,
      bevelThickness: 0.025,
      bevelSize: 0.025,
      bevelSegments: 2,
    })
  }, [])

  const rightGeom = useMemo(() => {
    return new ExtrudeGeometry(createYinSegmentShape(1.0, 0.5), {
      depth: 0.14,
      bevelEnabled: true,
      bevelThickness: 0.025,
      bevelSize: 0.025,
      bevelSegments: 2,
    })
  }, [])

  return (
    <>
      <mesh position={[-YIN_OFFSET_X, y, 0]} scale={[1, 1, 0.2]} material={material} geometry={leftGeom} />
      <mesh position={[YIN_OFFSET_X, y, 0]} scale={[1, 1, 0.2]} material={material} geometry={rightGeom} />
    </>
  )
}

// =============================================================================
// Root
// =============================================================================

const Hexagram3D = memo(function Hexagram3D({ bits }: Hexagram3DProps) {
  if (bits.length !== 6) {
    console.warn('Hexagram3D: bits must be exactly 6 characters')
  }

  return (
    <group>
      {bits.split('').map((bit, index) => {
        const isYang = bit === '1'
        if (isYang) {
          return <Yang key={index} index={index} />
        }
        return <Yin key={index} index={index} />
      })}
    </group>
  )
})

export default Hexagram3D