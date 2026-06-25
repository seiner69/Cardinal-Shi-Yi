import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { useEffect, useMemo, useRef } from 'react'
import { Group } from 'three'
import { OrbitControls as ThreeOrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import Hexagram3D from './components/Hexagram3D'
import OverlayUI from './components/OverlayUI'
import { useStore } from './store/useStore'

function OrbitControls() {
  const { camera, gl } = useThree()
  const controls = useMemo(() => {
    const nextControls = new ThreeOrbitControls(camera, gl.domElement)
    nextControls.enableDamping = true
    nextControls.dampingFactor = 0.08
    nextControls.enablePan = false
    nextControls.minDistance = 4
    nextControls.maxDistance = 12
    return nextControls
  }, [camera, gl.domElement])

  useFrame(() => controls.update())

  useEffect(() => () => controls.dispose(), [controls])

  return null
}

function RotatingGroup({ children, isLoading }: { children: React.ReactNode; isLoading: boolean }) {
  const groupRef = useRef<Group>(null)
  const floatRef = useRef(0)
  const { size } = useThree()
  const isMobile = size.width < 640
  const baseY = isMobile ? 1.35 : 0
  const baseScale = isMobile ? 0.82 : 1

  useEffect(() => {
    if (!groupRef.current) return
    groupRef.current.scale.setScalar(baseScale)
    groupRef.current.position.y = baseY
  }, [baseScale, baseY])

  useFrame((_, delta) => {
    if (document.hidden) return
    if (groupRef.current) {
      const frameDelta = Math.min(delta, 0.033)
      groupRef.current.rotation.y += frameDelta * (isLoading ? 1.5 : 0.42)
      if (isLoading) {
        floatRef.current += frameDelta * 3
        groupRef.current.position.y = baseY + Math.sin(floatRef.current) * 0.15
      } else {
        groupRef.current.position.y = baseY
      }
    }
  })

  return <group ref={groupRef}>{children}</group>
}

function Scene() {
  const fsmData = useStore((s) => s.fsmData)
  const physicsInputs = useStore((s) => s.physicsInputs)
  const physicsSnapshot = useStore((s) => s.physicsSnapshot)
  const viewMode = useStore((s) => s.viewMode)
  const isLoading = useStore((s) => s.isLoading)

  const analysisBits = fsmData
    ? fsmData.inner_bits + fsmData.outer_bits
    : null
  const bits = viewMode === 'analysis'
    ? (analysisBits && analysisBits.length === 6 ? analysisBits : '010101')
    : (physicsSnapshot?.bits ?? physicsInputs.bits ?? '010101')

  return (
    <>
      <color attach="background" args={['#f5f3ee']} />
      <ambientLight intensity={1.35} />
      <directionalLight position={[5, 10, 5]} intensity={1.9} />
      <directionalLight position={[-4, 4, -3]} intensity={0.55} color="#b7d8d4" />
      <OrbitControls />
      <RotatingGroup isLoading={isLoading}>
        <Hexagram3D bits={bits} isLoading={isLoading} />
      </RotatingGroup>
    </>
  )
}

function App() {
  return (
    <div className="relative h-screen w-screen overflow-hidden bg-[#f5f3ee]">
      <div className="scene-canvas absolute inset-0">
        <Canvas
          camera={{ position: [0, 0, 7], fov: 48 }}
          dpr={[1, 1.5]}
          gl={{ antialias: true, alpha: false, powerPreference: 'high-performance' }}
        >
          <Scene />
        </Canvas>
      </div>
      <OverlayUI />
    </div>
  )
}

export default App
