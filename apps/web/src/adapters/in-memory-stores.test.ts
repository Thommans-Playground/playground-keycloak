// The in-memory stores must keep the same promises as any other store: see store-contract.ts.
import { InMemoryLoginAttemptStore, InMemorySessionStore } from "./in-memory-stores.ts";
import { loginAttemptStoreContract, sessionStoreContract } from "./store-contract.ts";

loginAttemptStoreContract("InMemoryLoginAttemptStore", () => new InMemoryLoginAttemptStore());
sessionStoreContract("InMemorySessionStore", () => new InMemorySessionStore());
