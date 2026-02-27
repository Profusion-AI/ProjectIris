// SPDX-License-Identifier: Apache-2.0

export type PlayerSessionState =
  | "idle"
  | "connecting"
  | "connected"
  | "streaming_ready"
  | "degraded"
  | "failed";

export interface PlayerStatusModel {
  state: PlayerSessionState;
  sessionId?: string;
  transportMode?: "realtime" | "buffered";
  latencyMs?: number;
  message?: string;
  updatedAt: string;
}

export type PlayerAction =
  | "CONNECT_REQUEST"
  | "CONNECT_SUCCESS"
  | "STREAM_READY"
  | "DEGRADE_NOTICE"
  | "FAILURE"
  | "RESET";

export interface DemoTelemetryEvent {
  name:
    | "ui_loaded"
    | "connect_started"
    | "connect_succeeded"
    | "stream_ready"
    | "error_shown";
  timestamp: string;
  sessionId?: string;
  meta?: Record<string, unknown>;
}
