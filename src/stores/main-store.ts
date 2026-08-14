import { defineStore, acceptHMRUpdate } from 'pinia'
import type { components } from '@/dto/api'
import type { TriggerSchema } from '@/types/trigger-schema'

export type KioskState = {
  payment_enabled: boolean
  price: number
  denominations: number[]
  readiness: Record<'camera' | 'printer' | 'disk' | 'cloud' | 'payment_hardware' | 'password_changed' | 'ready', boolean>
  test_grant_valid: boolean
  session: null | {
    id: number
    mode: 'paid' | 'test'
    state: 'collecting' | 'paid' | 'capturing' | 'presenting' | 'completed' | 'forfeited' | 'voided'
    credit: number
    remaining_balance: number
    overpayment: number
    seconds_remaining: number | null
    result_ids: string[]
    retakes_remaining: number
    prints_remaining: number
    printable_result_id: string | null
  }
}

function defaultOnetimeInformation(): components['schemas']['SseEventOnetimeInformationRecord'] {
  return {
    version: '',
    platform_system: '',
    platform_release: '',
    platform_machine: '',
    platform_python_version: '',
    platform_node: '',
    platform_cpu_count: null,
    model: '',
    data_directory: '',
    python_executable: '',
    disk: {},
  }
}

function defaultIntervalInformation(): components['schemas']['SseEventIntervalInformationRecord'] {
  return {
    cpu_percent: 0,
    memory: {},
    cma: {},
    backends: {},
    stats_counter: [],
    limits_counter: [],
    battery_percent: null,
    temperatures: {},
    mediacollection: {},
    plugins: [],
    pi_throttled_flags: {},
  }
}

export const useMainStore = defineStore('main-store', {
  state: () => ({
    logrecords: [] as object[],

    information_onetime: defaultOnetimeInformation(),
    information_interval: defaultIntervalInformation(),

    lastAction: null as TriggerSchema | null,
    kioskState: null as KioskState | null,
    kioskTestGrant: null as string | null,

    //   /* plugins stats */
    //   plugins: {},
    // },
  }),
  actions: {},
  getters: {},
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useMainStore, import.meta.hot))
}
