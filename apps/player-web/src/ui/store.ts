// SPDX-License-Identifier: Apache-2.0
import type { PlayerAction, PlayerStatusModel } from "./types.js";

type Listener = (model: PlayerStatusModel) => void;

function now(): string {
  return new Date().toISOString();
}

function reduce(
  state: PlayerStatusModel,
  action: PlayerAction,
  payload?: Partial<PlayerStatusModel>,
): PlayerStatusModel {
  switch (action) {
    case "CONNECT_REQUEST":
      return { state: "connecting", updatedAt: now() };
    case "CONNECT_SUCCESS":
      return { ...state, state: "connected", ...payload, updatedAt: now() };
    case "STREAM_READY":
      return { ...state, state: "streaming_ready", ...payload, updatedAt: now() };
    case "DEGRADE_NOTICE":
      return { ...state, state: "degraded", ...payload, updatedAt: now() };
    case "FAILURE":
      return { ...state, state: "failed", ...payload, updatedAt: now() };
    case "RESET":
      return { state: "idle", updatedAt: now() };
  }
}

export class PlayerStore {
  private model: PlayerStatusModel;
  private listeners: Listener[] = [];

  constructor() {
    this.model = { state: "idle", updatedAt: now() };
  }

  getModel(): PlayerStatusModel {
    return this.model;
  }

  dispatch(action: PlayerAction, payload?: Partial<PlayerStatusModel>): void {
    this.model = reduce(this.model, action, payload);
    for (const listener of this.listeners) {
      listener(this.model);
    }
  }

  subscribe(listener: Listener): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== listener);
    };
  }
}
