import { GenerateResponse, SemesterGenConfig } from "@/types";

export const DEFAULT_CU_CAP = 5.5;
export const DEFAULT_SUMMER_CAP = 2;

export const genConfigKey = (planId: number | string) => `PDP-${planId}-generate`;

export interface StoredGenConfig {
  enabled: boolean;
  allowSummer: boolean;
  semesters: Record<string, SemesterGenConfig>;
  /** Requirement blocks the student dragged. Slot id to semester. */
  pinnedSlots?: Record<string, string>;
}

export const emptyGenConfig = (): StoredGenConfig => ({
  enabled: false,
  allowSummer: false,
  semesters: {},
});

/** Older builds stored this blob as a bare array of semester keys. Keep those keys. */
export function parseGenConfig(raw: string | null): StoredGenConfig {
  if (!raw) return emptyGenConfig();
  try {
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) {
      const semesters: Record<string, SemesterGenConfig> = {};
      parsed.forEach((key) => {
        if (typeof key === "string") {
          semesters[key] = {
            cuCap: key.endsWith("B") ? DEFAULT_SUMMER_CAP : DEFAULT_CU_CAP,
            gap: false,
          };
        }
      });
      return { enabled: false, allowSummer: false, semesters, pinnedSlots: {} };
    }
    if (parsed && typeof parsed === "object") {
      return {
        enabled: Boolean(parsed.enabled),
        allowSummer: Boolean(parsed.allowSummer),
        semesters: parsed.semesters && typeof parsed.semesters === "object" ? parsed.semesters : {},
        pinnedSlots: parsed.pinnedSlots && typeof parsed.pinnedSlots === "object" ? parsed.pinnedSlots : {},
      };
    }
  } catch {
    return emptyGenConfig();
  }
  return emptyGenConfig();
}

let requestSerial = 0;

/** Monotonic id so a slow response cannot overwrite a newer one. */
export function nextRequestId(): number {
  requestSerial += 1;
  return requestSerial;
}

export function isCurrentRequest(id: number, latest: number): boolean {
  return id === latest;
}

let published: GenerateResponse | null = null;
const proposalListeners = new Set<() => void>();

export function publishProposal(next: GenerateResponse | null) {
  published = next;
  proposalListeners.forEach((listener) => listener());
}

export function currentProposal() {
  return published;
}

export function subscribeProposal(listener: () => void) {
  proposalListeners.add(listener);
  return () => {
    proposalListeners.delete(listener);
  };
}
