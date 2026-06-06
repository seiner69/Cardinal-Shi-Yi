import axios from 'axios'
import { create } from 'zustand'
import { eventLabel } from '../utils/physicsLabels'

export interface BitAnalysis {
  bit_position: number
  value: string
  description: string
}

export interface EnergyFocus {
  focus_bit: number
  focus_description: string
}

export interface StressAnalysis {
  stress_type: string
  analysis: string
}

export interface FSMAnalysis {
  inner_system: string
  outer_system: string
  inner_bits: string
  outer_bits: string
  bit_analysis: BitAnalysis[]
  energy_focus: EnergyFocus
  stress_analysis: StressAnalysis
  mutation_suggestion: string
  target_hexagram: string
  hexagram_reason: string
  referenced_yao: string
  yao_interpretation: string
}

export interface RetrievalResult {
  hexagram_name: string | null
  text_type: string | null
  context: string | null
  content: string | null
  distance: number | null
}

export interface FSMNode {
  index: number
  name: string
  code: string
  physics_description: string
  entropy_S: number
  mass_M: number
}

export interface DeterministicResult {
  current_node: FSMNode
  max_stress_bit: number
  stress_type: string
  evolution_path: number
  evolution_path_name: string
  all_possible_moves: FSMNode[]
  next_state: FSMNode | null
}

export interface SimulateFlip {
  bit: number
  old_val: number
  new_val: number
  new_bits: string
  hexagram: string
  hex_index: number
  physics_name: string
  physics_desc: string
  entropy_S: number
}

export interface SimulateResponse {
  current: FSMNode
  flips: SimulateFlip[]
}

export interface EvolveResponse {
  current: FSMNode
  path?: number
  path_name?: string
  triggered_bit?: number
  stress_type?: string
  next_state?: FSMNode
  entropy_chain?: SimulateFlip[]
  operations?: Record<string, unknown>
  route?: {
    path_number: number
    path_name: string
    description: string
    result: unknown
  }
}

export interface InferResponse {
  fsm_analysis: FSMAnalysis & { deterministic?: DeterministicResult | null }
  retrieval_results: RetrievalResult[]
  physics_seed?: PhysicsInputs
}

export interface PhysicsTensor {
  e: number
  p: number
  t: number
}

export interface PhysicsLayer {
  bit: number
  B: number
  phase: '0' | '0*' | '1' | '1*'
  event: string
  ttl: number | null
  next_value: number
  sigma: number
  tensor: PhysicsTensor
  E: number
  P: number
  R: number
  R_base: number
  tau: number
  C: number
}

export interface PhysicsUncertainty {
  U_E: number
  U_P: number
  U_R: number
  U_tau: number
}

export interface PhysicsInputs {
  bits: string
  E: number[]
  P: number[]
  R: number[]
  tau: number[]
  C: number[]
  E_initial: number[]
  R_base: number[]
  U: PhysicsUncertainty
  delta_E_ext: number
  deadlock_flag: boolean
  time_in_state: number
  monte_carlo_N: number
}

export interface MonteCarloOutcome {
  bits: string
  probability: number
  count: number
  hexagram: string
}

export interface RouteAlternative {
  key: string
  operation: string
  bits: string
  hexagram?: string | null
  entropy_S?: number | null
}

export interface PhysicsSnapshot {
  bits: string
  inner_bits: string
  outer_bits: string
  hexagram: string
  entropy_S: number
  mass_M: number
  focus_bit: number
  event: string
  ttl: number | null
  next_bits: string
  selected_next_bits: string | null
  tensor: PhysicsTensor
  layers: PhysicsLayer[]
  interrupt: {
    focus_bit: number
    event: string
    ttl: number | null
    next_bits: string
    tensor: PhysicsTensor
  }
  route: {
    path_number: number
    path_name: string
    description: string
    next_bits: string | null
    alternatives: RouteAlternative[]
    result: unknown
  }
  confidence: {
    conf_input: number
    conf_m1: number
    U_E: number
    U_P: number
    U_R: number
    U_tau: number
  }
  monte_carlo: MonteCarloOutcome[]
}

export interface NodeInfo {
  bits: string
  E: number[]
  E_initial: number[]
  P: number[]
  tau: number[]
  R: number[]
  R_base: number[]
  conf_m1: number
}

export interface SSOTSimulation {
  currentBits: string
  nextBits: string | null
  transitionBit: number | null
  evolutionPath: number
  evolutionPathName: string
  entropyS: number
  confM1: number
}

type PhysicsLayerPatch = Partial<Pick<PhysicsLayer, 'E' | 'P' | 'R' | 'R_base' | 'tau' | 'C'>>
type PhysicsRoutePatch = Partial<Pick<PhysicsInputs, 'delta_E_ext' | 'deadlock_flag' | 'time_in_state' | 'monte_carlo_N'>>

interface StoreState {
  viewMode: 'analysis' | 'simulation' | 'evolution'
  isLoading: boolean
  inferError: string | null
  query: string
  fsmData: FSMAnalysis | null
  retrievalResults: RetrievalResult[]
  deterministic: DeterministicResult | null
  simulateFlips: SimulateFlip[]
  nodeInfo: NodeInfo | null
  ssotSimulation: SSOTSimulation | null
  physicsSeed: PhysicsInputs | null
  physicsInputs: PhysicsInputs
  physicsSnapshot: PhysicsSnapshot | null
  typewriterLogs: string[]
  isSimulating: boolean
  setViewMode: (mode: 'analysis' | 'simulation' | 'evolution') => void
  fetchInfer: (query: string) => Promise<void>
  simulateFlip: (bits: string) => Promise<SimulateFlip[]>
  evolve: (bits: string, path?: number) => Promise<EvolveResponse>
  fetchNodeInfo: (bits: string) => Promise<void>
  runPhysics: (inputs?: PhysicsInputs) => Promise<PhysicsSnapshot | null>
  applyPhysicsSeed: (seed?: PhysicsInputs | null, bitsOverride?: string) => void
  updatePhysicsBit: (bitIndex: number, value: number) => void
  updatePhysicsLayer: (bitIndex: number, patch: PhysicsLayerPatch) => void
  updatePhysicsUncertainty: (patch: Partial<PhysicsUncertainty>) => void
  updatePhysicsRoute: (patch: PhysicsRoutePatch) => void
  addTypewriterLog: (msg: string) => void
  setQuery: (query: string) => void
  reset: () => void
}

const DEFAULT_PHYSICS_INPUTS: PhysicsInputs = {
  bits: '101010',
  E: [1, 0.8, 0.2, 0.7, 0.4, 0.9],
  P: [0.1, 0.2, 0.3, 0.95, 0.2, 0.1],
  R: [0.1, 0.1, 0.12, 0.1, 0.1, 0.1],
  tau: [1, 1, 1, 1, 1, 1],
  C: [0.15, 0.15, 0.15, 0.15, 0.15, 0.15],
  E_initial: [1, 1, 1, 1, 1, 1],
  R_base: [0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
  U: { U_E: 0.05, U_P: 0.25, U_R: 0.05, U_tau: 0.05 },
  delta_E_ext: 0,
  deadlock_flag: false,
  time_in_state: 0,
  monte_carlo_N: 1000,
}

function normalizeBits(bits: string | undefined, fallback: string) {
  return bits && /^[01]{6}$/.test(bits) ? bits : fallback
}

function normalizeNumberArray(values: number[] | undefined, fallback: number[]) {
  if (!Array.isArray(values) || values.length !== 6) return [...fallback]
  return values.map((value, index) => Number.isFinite(value) ? value : fallback[index])
}

function normalizePhysicsInputs(seed: PhysicsInputs, bitsOverride?: string): PhysicsInputs {
  const bits = normalizeBits(bitsOverride, normalizeBits(seed.bits, DEFAULT_PHYSICS_INPUTS.bits))
  return {
    bits,
    E: normalizeNumberArray(seed.E, DEFAULT_PHYSICS_INPUTS.E),
    P: normalizeNumberArray(seed.P, DEFAULT_PHYSICS_INPUTS.P),
    R: normalizeNumberArray(seed.R, DEFAULT_PHYSICS_INPUTS.R),
    tau: normalizeNumberArray(seed.tau, DEFAULT_PHYSICS_INPUTS.tau),
    C: normalizeNumberArray(seed.C, DEFAULT_PHYSICS_INPUTS.C),
    E_initial: normalizeNumberArray(seed.E_initial, DEFAULT_PHYSICS_INPUTS.E_initial),
    R_base: normalizeNumberArray(seed.R_base, DEFAULT_PHYSICS_INPUTS.R_base),
    U: {
      U_E: Number.isFinite(seed.U?.U_E) ? seed.U.U_E : DEFAULT_PHYSICS_INPUTS.U.U_E,
      U_P: Number.isFinite(seed.U?.U_P) ? seed.U.U_P : DEFAULT_PHYSICS_INPUTS.U.U_P,
      U_R: Number.isFinite(seed.U?.U_R) ? seed.U.U_R : DEFAULT_PHYSICS_INPUTS.U.U_R,
      U_tau: Number.isFinite(seed.U?.U_tau) ? seed.U.U_tau : DEFAULT_PHYSICS_INPUTS.U.U_tau,
    },
    delta_E_ext: Number.isFinite(seed.delta_E_ext) ? seed.delta_E_ext : DEFAULT_PHYSICS_INPUTS.delta_E_ext,
    deadlock_flag: Boolean(seed.deadlock_flag),
    time_in_state: Number.isFinite(seed.time_in_state) ? Math.max(0, Math.round(seed.time_in_state)) : 0,
    monte_carlo_N: Number.isFinite(seed.monte_carlo_N)
      ? Math.max(1, Math.min(10000, Math.round(seed.monte_carlo_N)))
      : DEFAULT_PHYSICS_INPUTS.monte_carlo_N,
  }
}

function patchArray(values: number[], index: number, value: number) {
  const next = [...values]
  next[index] = value
  return next
}

function snapshotToNodeInfo(snapshot: PhysicsSnapshot, inputs: PhysicsInputs): NodeInfo {
  return {
    bits: snapshot.bits,
    E: snapshot.layers.map(layer => layer.E),
    E_initial: inputs.E_initial,
    P: snapshot.layers.map(layer => layer.P),
    tau: snapshot.layers.map(layer => layer.tau),
    R: snapshot.layers.map(layer => layer.R),
    R_base: snapshot.layers.map(layer => layer.R_base),
    conf_m1: snapshot.confidence.conf_input,
  }
}

function clearPhysicsResult() {
  return {
    physicsSnapshot: null,
    ssotSimulation: null,
  }
}

export const useStore = create<StoreState>((set, get) => ({
  viewMode: 'analysis',
  isLoading: false,
  inferError: null,
  query: '',
  fsmData: null,
  retrievalResults: [],
  deterministic: null,
  simulateFlips: [],
  nodeInfo: null,
  ssotSimulation: null,
  physicsSeed: null,
  physicsInputs: DEFAULT_PHYSICS_INPUTS,
  physicsSnapshot: null,
  typewriterLogs: [],
  isSimulating: false,

  setViewMode: mode => set({ viewMode: mode }),

  fetchInfer: async (query: string) => {
    set({ isLoading: true, inferError: null, physicsSeed: null })
    try {
      const { data } = await axios.post<InferResponse>('/api/infer', { query })
      set({
        fsmData: data.fsm_analysis,
        retrievalResults: data.retrieval_results,
        deterministic: data.fsm_analysis?.deterministic ?? null,
        physicsSeed: data.physics_seed ? normalizePhysicsInputs(data.physics_seed) : null,
        isLoading: false,
      })
    } catch (err) {
      console.error('infer error:', err)
      set({
        isLoading: false,
        inferError: err instanceof Error ? err.message : '分析请求失败',
      })
    }
  },

  simulateFlip: async (bits: string) => {
    try {
      const { data } = await axios.get<SimulateResponse>('/api/simulate', {
        params: { bits },
      })
      set({ simulateFlips: data.flips })
      return data.flips
    } catch (err) {
      console.error('simulate error:', err)
      return []
    }
  },

  evolve: async (bits: string, path?: number) => {
    try {
      const params: Record<string, string | number | boolean> = { bits }
      if (path !== undefined) params.path = path
      const { data } = await axios.get<EvolveResponse>('/api/evolve', { params })
      return data
    } catch (err) {
      console.error('evolve error:', err)
      throw err
    }
  },

  fetchNodeInfo: async (bits: string) => {
    try {
      const { data } = await axios.get<NodeInfo>('/api/node', { params: { bits } })
      set({ nodeInfo: data })
    } catch (err) {
      console.error('node error:', err)
    }
  },

  runPhysics: async (inputs?: PhysicsInputs) => {
    const currentInputs = inputs ?? get().physicsInputs
    set({ isSimulating: true })
    try {
      const { data } = await axios.post<PhysicsSnapshot>('/api/physics', currentInputs)
      set({
        physicsInputs: currentInputs,
        physicsSnapshot: data,
        nodeInfo: snapshotToNodeInfo(data, currentInputs),
        ssotSimulation: {
          currentBits: data.bits,
          nextBits: data.selected_next_bits,
          transitionBit: data.focus_bit,
          evolutionPath: data.route.path_number,
          evolutionPathName: data.route.path_name,
          entropyS: data.entropy_S,
          confM1: data.confidence.conf_input,
        },
        typewriterLogs: [
          `B${data.focus_bit} ${eventLabel(data.event)}，TTL=${data.ttl ?? '无穷'}，硬中断=${data.next_bits}`,
          `路径${data.route.path_number} ${data.route.path_name}，后继=${data.selected_next_bits ?? '多后继'}`,
          `T(e,p,t)=(${data.tensor.e.toFixed(2)},${data.tensor.p},${data.tensor.t.toFixed(2)})`,
        ],
        isSimulating: false,
      })
      return data
    } catch (err) {
      console.error('physics error:', err)
      set({ isSimulating: false })
      return null
    }
  },

  applyPhysicsSeed: (seed, bitsOverride) => {
    set(state => {
      const source = seed ?? state.physicsSeed ?? state.physicsInputs
      return {
        ...clearPhysicsResult(),
        physicsInputs: normalizePhysicsInputs(source, bitsOverride),
        nodeInfo: null,
      }
    })
  },

  updatePhysicsBit: (bitIndex: number, value: number) => {
    set(state => {
      const bits = state.physicsInputs.bits.split('')
      bits[bitIndex - 1] = String(value)
      return {
        ...clearPhysicsResult(),
        physicsInputs: { ...state.physicsInputs, bits: bits.join('') },
      }
    })
  },

  updatePhysicsLayer: (bitIndex, patch) => {
    const idx = bitIndex - 1
    set(state => {
      const next = { ...state.physicsInputs }
      if (patch.E !== undefined) {
        next.E = patchArray(next.E, idx, patch.E)
        next.E_initial = patchArray(next.E_initial, idx, Math.max(next.E_initial[idx], patch.E))
      }
      if (patch.P !== undefined) next.P = patchArray(next.P, idx, patch.P)
      if (patch.R !== undefined) next.R = patchArray(next.R, idx, patch.R)
      if (patch.R_base !== undefined) next.R_base = patchArray(next.R_base, idx, patch.R_base)
      if (patch.tau !== undefined) next.tau = patchArray(next.tau, idx, patch.tau)
      if (patch.C !== undefined) next.C = patchArray(next.C, idx, patch.C)
      return {
        ...clearPhysicsResult(),
        physicsInputs: next,
      }
    })
  },

  updatePhysicsUncertainty: patch => {
    set(state => ({
      ...clearPhysicsResult(),
      physicsInputs: {
        ...state.physicsInputs,
        U: { ...state.physicsInputs.U, ...patch },
      },
    }))
  },

  updatePhysicsRoute: patch => {
    set(state => ({
      ...clearPhysicsResult(),
      physicsInputs: { ...state.physicsInputs, ...patch },
    }))
  },

  addTypewriterLog: (msg: string) => {
    set(state => ({
      typewriterLogs: [...state.typewriterLogs, msg],
    }))
  },

  setQuery: (query: string) => set({ query }),

  reset: () => set({
    viewMode: 'analysis',
    isLoading: false,
    inferError: null,
    query: '',
    fsmData: null,
    retrievalResults: [],
    deterministic: null,
    simulateFlips: [],
    nodeInfo: null,
    ssotSimulation: null,
    physicsSeed: null,
    physicsInputs: DEFAULT_PHYSICS_INPUTS,
    physicsSnapshot: null,
    typewriterLogs: [],
    isSimulating: false,
  }),
}))
