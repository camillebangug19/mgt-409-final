export type ChatTurn = {
  message: string
  quick_replies: string[]
  done: boolean
  section: string | null
  sections: string[]
  section_index: number
  progress: number
  filled: number
  total: number
}

export type Message = {
  role: 'bot' | 'user'
  text: string
}
