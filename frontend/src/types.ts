export type ChatTurn = {
  message: string
  quick_replies: string[]
  done: boolean
  next_slot: string | null
  mood: SunnyMood
  section: string | null
  sections: string[]
  section_index: number
  progress: number
  filled: number
  total: number
}

export type SunnyMood = 'hi' | 'thinking' | 'cheer' | 'calm'

export type Message = {
  role: 'bot' | 'user'
  text: string
  mood?: SunnyMood
}

export type Source = {
  id: string
  publisher: string
  title: string
  source_url: string
}

export type CheapOption = {
  id: string
  label: string
  cost_band: string
  source: Source | null
}

export type SelfCheckItem = {
  item_id: string
  label: string
}

export type Step = {
  id: string
  title: string
  points_gain: number
  why: string
  est_minutes: number
  est_cost_band: string
  how_to: string[]
  self_check: SelfCheckItem[]
  sources: Source[]
  cheap_options: CheapOption[]
  medical_note: string | null
}

export type CategoryRow = {
  category: string
  earned: number
  max_points: number
}

export type LocalResource = {
  state: string
  type: string
  name: string
  url: string
  verified: boolean
}

export type Plan = {
  score: number
  label: string
  earned: number
  max_points: number
  breakdown: CategoryRow[]
  steps: Step[]
  completed_step_ids: string[]
  local_resources: { state: string | null; is_fallback: boolean; resources: LocalResource[] }
  quantities: {
    days: number
    people: number
    water_gallons: number
    food_days: number
    pets: number
    pet_water_gallons: number
    meds_reminder: string | null
  }
  rubric_note: string
  disclaimer: string
  flagged: string[]
  completion?: { step_id: string; score_before: number; score_after: number; delta: number; credited: string[] }
}

export type SessionStatus = {
  found: boolean
  survey_done?: boolean
  progress?: number
  answered?: number
  remaining?: number
  first_score?: number | null
  latest_score?: number | null
  completed_steps?: number
  people?: number
  pets?: number
  state?: string | null
  started_at?: string
}
