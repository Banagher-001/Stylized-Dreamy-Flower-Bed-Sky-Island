export type AboutStationId = 'A1' | 'A2' | 'A3';
export type CategoryId = 'G1' | 'G2' | 'G3' | 'G4' | 'G5' | 'G6' | 'G7';
export type CategoryFilter = 'all' | CategoryId;
export type AboutLayout = 'immersive' | 'stable';

export interface ToolCard {
  readonly id: string;
  readonly name: string;
  readonly use: string;
  readonly detail: string;
  readonly tags: readonly [string, string];
  readonly category: CategoryId;
  readonly kind: 'tool' | 'practice';
  readonly recommendationOrder: number;
  readonly categoryOrder: number;
  readonly initialEntryRank: number | null;
  /** A dimension placeholder; final visual marks belong to step 5. */
  readonly mark: string;
}

export interface ToolCategory {
  readonly id: CategoryId;
  readonly name: string;
  readonly cardIds: readonly string[];
}

export interface AboutContent {
  readonly identity: {
    readonly eyebrow: string;
    readonly title: string;
    readonly role: string;
    readonly paragraphs: readonly string[];
    readonly keywords: readonly string[];
    readonly alias: string;
  };
  readonly experience: {
    readonly eyebrow: string;
    readonly title: string;
    readonly entries: readonly { readonly label: string; readonly company: string; readonly role?: string }[];
    readonly process: readonly { readonly name: string; readonly detail: string }[];
    readonly education: string;
  };
  readonly tools: { readonly eyebrow: string; readonly title: string; readonly introduction: string };
  readonly categories: readonly ToolCategory[];
  readonly cards: readonly ToolCard[];
  readonly controls: Readonly<Record<string, string>>;
}

export interface TrackPosition {
  readonly anchorId: string;
  readonly offsetRatio: number;
  readonly scrollLeft: number;
  readonly viewportWidth: number;
}

export interface CardsSnapshot {
  readonly category: CategoryFilter;
  readonly activeId: string;
  readonly expandedId: string | null;
  readonly position: TrackPosition;
}

export interface ToolBrowserSnapshot {
  readonly mode: 'cards' | 'all';
  readonly cards: CardsSnapshot;
  readonly track?: CardTrackSnapshot;
}

export interface CardTrackSnapshot {
  readonly position: TrackPosition;
  readonly program: boolean;
  readonly cycled: boolean;
  readonly enabled: boolean;
  readonly decided: boolean;
  readonly bend?: number;
  readonly direction?: -1 | 1;
  /** Temporary offscreen spacing used only before the first safe seam passage. */
  readonly leadIn?: number;
}
export interface CardTrackContext {
  readonly active: boolean;
  readonly allowed: boolean;
  readonly automatic: boolean;
  readonly top: number;
  readonly bottom: number;
}

export interface AboutSnapshot {
  readonly station: AboutStationId;
  readonly identityOpen: boolean;
  readonly experienceOpen: boolean;
  readonly tools: ToolBrowserSnapshot;
}

export interface AboutViewOptions {
  /** The host decides when and how to interrupt a real tour (steps 4/13). */
  readonly onInteraction?: () => void;
  readonly onLayoutChange?: () => void;
  readonly onContinue?: () => void;
  readonly onToolModeChange?: (mode: 'cards' | 'all') => void;
  /** Entrance readiness changes wake the guide, without requesting capacity probes. */
  readonly onEntranceChange?: () => void;
  /** The continuation hint shares the tool browser's current input and reading state. */
  readonly onToolLeaveHint?: (text: string) => void;
}

export interface CardEntranceContext {
  readonly active: boolean;
  readonly enabled: boolean;
  readonly revealed: boolean;
}

/** Actual host reading, never capacity probes or wheel guesses. */
export interface CardDepartureContext {
  readonly active: boolean;
  readonly enabled: boolean;
  readonly progress: number;
  readonly readable: boolean;
}
