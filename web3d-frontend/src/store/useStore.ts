import axios from 'axios'

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
}

// SSOT Node Info from /api/node
export interface NodeInfo {
  bits: string
  E: number[]
  P: number[]
  tau: number[]
  R: number[]
  conf_m1: number
}

// SSOT Simulation state
export interface SSOTSimulation {
  currentBits: string
  nextBits: string | null
  transitionBit: number | null
  evolutionPath: number
  evolutionPathName: string
  entropyS: number
  confM1: number
}

interface StoreState {
  isLoading: boolean
  query: string
  fsmData: FSMAnalysis | null
  retrievalResults: RetrievalResult[]
  deterministic: DeterministicResult | null
  simulateFlips: SimulateFlip[]
  // SSOT simulation state
  nodeInfo: NodeInfo | null
  ssotSimulation: SSOTSimulation | null
  typewriterLogs: string[]
  isSimulating: boolean
  // Actions
  fetchInfer: (query: string) => Promise<void>
  simulateFlip: (bits: string) => Promise<SimulateFlip[]>
  evolve: (bits: string, path?: number) => Promise<EvolveResponse>
  fetchNodeInfo: (bits: string) => Promise<void>
  addTypewriterLog: (msg: string) => void
  setQuery: (query: string) => void
  reset: () => void
}

import { create } from 'zustand'

export const useStore = create<StoreState>((set) => ({
  isLoading: false,
  query: '',
  fsmData: null,
  retrievalResults: [],
  deterministic: null,
  simulateFlips: [],
  // SSOT
  nodeInfo: null,
  ssotSimulation: null,
  typewriterLogs: [],
  isSimulating: false,

  fetchInfer: async (query: string) => {
    set({ isLoading: true })
    try {
      const { data } = await axios.post<InferResponse>('/api/infer', { query })
      set({
        fsmData: data.fsm_analysis,
        retrievalResults: data.retrieval_results,
        deterministic: data.fsm_analysis?.deterministic ?? null,
        isLoading: false,
      })
    } catch (err) {
      console.error('infer error:', err)
      set({ isLoading: false })
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
      const { data } = await axios.get<{
        bits: string
        E: number[]
        P: number[]
        tau: number[]
        R: number[]
        conf_m1: number
      }>('/api/node', { params: { bits } })
      set({
        nodeInfo: {
          bits: data.bits,
          E: data.E,
          P: data.P,
          tau: data.tau,
          R: data.R,
          conf_m1: data.conf_m1,
        },
      })
    } catch (err) {
      console.error('node error:', err)
    }
  },

  addTypewriterLog: (msg: string) => {
    set(state => ({
      typewriterLogs: [...state.typewriterLogs, msg],
    }))
  },

  setQuery: (query: string) => set({ query }),

  reset: () => set({
    isLoading: false,
    query: '',
    fsmData: null,
    retrievalResults: [],
    deterministic: null,
    simulateFlips: [],
    nodeInfo: null,
    ssotSimulation: null,
    typewriterLogs: [],
    isSimulating: false,
  }),
}))
