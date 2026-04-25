import { Canvas } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import { useRef } from 'react'
import { Group } from 'three'
import { useFrame } from '@react-three/fiber'
import Hexagram3D from './components/Hexagram3D'
import OverlayUI from './components/OverlayUI'
import { useStore } from './store/useStore'

function RotatingGroup({ children, isLoading }: { children: React.ReactNode; isLoading: boolean }) {
  const groupRef = useRef<Group>(null)
  const floatRef = useRef(0)

  useFrame((_, delta) => {
    if (groupRef.current) {
      groupRef.current.rotation.y += delta * (isLoading ? 1.5 : 0.5)
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
  const isLoading = useStore((s) => s.isLoading)

  const bits = fsmData
    ? fsmData.inner_bits + fsmData.outer_bits
    : '010101'

  return (
    <>
      {/* 古宣纸白底 */}
      <color attach="background" args={['#f4f4f0']} />
      {/* 柔和日光环境光 */}
      <ambientLight intensity={1.5} />
      {/* 主高光 */}
      <directionalLight position={[5, 10, 5]} intensity={2} />
      <OrbitControls />
      <RotatingGroup isLoading={isLoading}>
        <Hexagram3D bits={bits} isLoading={isLoading} />
      </RotatingGroup>
    </>
  )
}

function App() {
  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      <Canvas>
        <Scene />
      </Canvas>
      <OverlayUI />
    </div>
  )
}

export default App