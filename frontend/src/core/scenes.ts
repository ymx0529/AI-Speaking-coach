export interface SceneConfig {
  name: string
  name_zh: string
  personas: Record<string, { name: string }>
}

export const SCENES: Record<string, SceneConfig> = {
  interview: {
    name: 'Job Interview',
    name_zh: '求职面试',
    personas: { strict_interviewer: { name: 'Alex' } },
  },
  restaurant: {
    name: 'Restaurant Order',
    name_zh: '餐厅点餐',
    personas: { friendly_waiter: { name: 'Sam' } },
  },
  meeting: {
    name: 'Business Meeting',
    name_zh: '商务会议',
    personas: { colleague: { name: 'Jordan' } },
  },
  custom: {
    name: 'Custom Scenario',
    name_zh: '自定义场景',
    personas: { adaptive_coach: { name: 'Coach' } },
  },
}
