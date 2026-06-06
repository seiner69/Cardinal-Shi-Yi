import { Canvas } from '@react-three/fiber'
import { useFrame, useThree } from '@react-three/fiber'
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

  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * (isLoading ? 1.5 : 0.42)
      if (isLoading) {
        floatRef.current += delta * 3
        groupRef.current.position.y = Math.sin(floatRef.current) * 0.15
      } else {
        groupRef.current.position.y = 0
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
      <Canvas>
        <Scene />
      </Canvas>
      <OverlayUI />
    </div>
  )
}

export default App
