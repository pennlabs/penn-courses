import { openDB, DBSchema } from "idb";

interface AutocompleteDB extends DBSchema {
  autocomplete: {
    key: string;
    value: Uint8Array;
  };
}

export async function getDB() {
  return openDB<AutocompleteDB>("autocomplete-db", 1, {
    upgrade(db) {
      db.createObjectStore("autocomplete");
    },
  });
}

export async function setAutocomplete(data: Uint8Array) {
  const db = await getDB();
  await db.put("autocomplete", data, "data");
}

export async function getAutocomplete(): Promise<Uint8Array | undefined> {
  const db = await getDB();
  return db.get("autocomplete", "data");
}
