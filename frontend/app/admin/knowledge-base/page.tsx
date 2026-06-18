"use client";

import { useEffect, useState } from "react";
import {
  activateKnowledgeItem,
  createKnowledgeItem,
  deactivateKnowledgeItem,
  deleteKnowledgeItem,
  getKnowledgeItems,
  seedKnowledge,
  updateKnowledgeItem,
} from "@/lib/admin";
import { getUser } from "@/lib/auth";
import type { KnowledgeItem, KnowledgeItemInput } from "@/lib/types";

const CATEGORIES = [
  "clinic_info", "branches", "services_prices", "doctors", "doctor_schedule",
  "faq", "preparation_instructions", "operator_rules", "emergency_policy",
];

const EMPTY: KnowledgeItemInput = {
  category: "faq",
  title: "",
  content_uz: "",
  content_ru: "",
  tags: [],
  is_active: true,
};

export default function KnowledgeBasePage() {
  const role = getUser()?.role;
  const canManage = role === "super_admin" || role === "admin";
  const canSeed = role === "super_admin";

  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [category, setCategory] = useState("");
  const [activeOnly, setActiveOnly] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  // form state: null = closed, otherwise editing id (or "new")
  const [editing, setEditing] = useState<number | "new" | null>(null);
  const [form, setForm] = useState<KnowledgeItemInput>(EMPTY);
  const [tagsText, setTagsText] = useState("");
  const [saving, setSaving] = useState(false);

  function load() {
    setLoading(true);
    setError(null);
    getKnowledgeItems({ category: category || undefined, active_only: activeOnly })
      .then(setItems)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(load, [category, activeOnly]); // eslint-disable-line react-hooks/exhaustive-deps

  const visible = items.filter((it) => {
    if (!searchTerm.trim()) return true;
    const q = searchTerm.toLowerCase();
    return (
      it.title.toLowerCase().includes(q) ||
      (it.tags ?? []).some((t) => t.toLowerCase().includes(q))
    );
  });

  function openCreate() {
    setForm(EMPTY);
    setTagsText("");
    setEditing("new");
    setMessage(null);
  }

  function openEdit(it: KnowledgeItem) {
    setForm({
      category: it.category,
      title: it.title,
      content_uz: it.content_uz,
      content_ru: it.content_ru,
      tags: it.tags ?? [],
      is_active: it.is_active,
    });
    setTagsText((it.tags ?? []).join(", "));
    setEditing(it.id);
    setMessage(null);
  }

  function validate(): string | null {
    if (!form.category) return "Category is required";
    if (!form.title.trim()) return "Title is required";
    if (!form.content_uz.trim() && !form.content_ru.trim()) return "Provide content in Uzbek or Russian";
    return null;
  }

  async function onSave(e: React.FormEvent) {
    e.preventDefault();
    const v = validate();
    if (v) {
      setError(v);
      return;
    }
    setSaving(true);
    setError(null);
    const payload: KnowledgeItemInput = {
      ...form,
      tags: tagsText.split(",").map((t) => t.trim()).filter(Boolean),
    };
    try {
      if (editing === "new") await createKnowledgeItem(payload);
      else if (typeof editing === "number") await updateKnowledgeItem(editing, payload);
      setMessage("Saved successfully.");
      setEditing(null);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function act(fn: () => Promise<unknown>, ok: string) {
    setError(null);
    try {
      await fn();
      setMessage(ok);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    }
  }

  if (!canManage) {
    return <p className="text-sm text-red-600">Forbidden: knowledge base management is for admins.</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Knowledge base</h1>
        <div className="flex gap-2">
          <button onClick={openCreate} className="rounded bg-blue-600 px-3 py-1.5 text-sm text-white">
            New item
          </button>
          {canSeed && (
            <button
              onClick={() => act(() => seedKnowledge(), "Seeded demo clinic.")}
              className="rounded border px-3 py-1.5 text-sm hover:bg-gray-100"
            >
              Seed demo clinic
            </button>
          )}
        </div>
      </div>

      {message && <p className="text-sm text-green-700">{message}</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex flex-wrap gap-3 text-sm">
        <label className="flex items-center gap-1">
          Category
          <select className="rounded border px-2 py-1" value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">all</option>
            {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
        <label className="flex items-center gap-1">
          <input type="checkbox" checked={activeOnly} onChange={(e) => setActiveOnly(e.target.checked)} />
          active only
        </label>
        <input
          className="rounded border px-2 py-1"
          placeholder="Search title or tag"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {editing !== null && (
        <form onSubmit={onSave} className="space-y-2 rounded-lg border bg-white p-4 text-sm">
          <div className="font-medium">{editing === "new" ? "Create item" : `Edit item #${editing}`}</div>
          <div className="flex flex-wrap gap-2">
            <label className="flex flex-col gap-1">
              <span className="text-xs text-gray-500">Category *</span>
              <select className="rounded border px-2 py-1" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </label>
            <label className="flex flex-1 flex-col gap-1">
              <span className="text-xs text-gray-500">Title *</span>
              <input className="rounded border px-2 py-1" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
            </label>
          </div>
          <label className="flex flex-col gap-1">
            <span className="text-xs text-gray-500">Content (Uzbek)</span>
            <textarea className="rounded border px-2 py-1" rows={2} value={form.content_uz} onChange={(e) => setForm({ ...form, content_uz: e.target.value })} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-xs text-gray-500">Content (Russian)</span>
            <textarea className="rounded border px-2 py-1" rows={2} value={form.content_ru} onChange={(e) => setForm({ ...form, content_ru: e.target.value })} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-xs text-gray-500">Tags (comma separated)</span>
            <input className="rounded border px-2 py-1" value={tagsText} onChange={(e) => setTagsText(e.target.value)} />
          </label>
          <label className="flex items-center gap-1">
            <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
            active
          </label>
          <div className="flex gap-2">
            <button type="submit" disabled={saving} className="rounded bg-blue-600 px-3 py-1.5 text-white disabled:opacity-50">
              {saving ? "Saving..." : "Save"}
            </button>
            <button type="button" onClick={() => setEditing(null)} className="rounded border px-3 py-1.5 hover:bg-gray-100">
              Cancel
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : visible.length === 0 ? (
        <p className="text-sm text-gray-400">No knowledge items.</p>
      ) : (
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="py-2">Title</th>
              <th>Category</th>
              <th>Tags</th>
              <th>Active</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((it) => (
              <tr key={it.id} className="border-b align-top hover:bg-gray-50">
                <td className="py-2 font-medium">{it.title}</td>
                <td>{it.category}</td>
                <td className="text-gray-500">{(it.tags ?? []).join(", ")}</td>
                <td>{it.is_active ? "yes" : "no"}</td>
                <td className="space-x-1 whitespace-nowrap">
                  <button className="rounded border px-2 py-0.5" onClick={() => openEdit(it)}>Edit</button>
                  {it.is_active ? (
                    <button className="rounded border px-2 py-0.5" onClick={() => act(() => deactivateKnowledgeItem(it.id), "Deactivated.")}>Deactivate</button>
                  ) : (
                    <button className="rounded border px-2 py-0.5" onClick={() => act(() => activateKnowledgeItem(it.id), "Activated.")}>Activate</button>
                  )}
                  <button
                    className="rounded border border-red-300 px-2 py-0.5 text-red-700"
                    onClick={() => {
                      if (window.confirm(`Permanently delete "${it.title}"?`)) act(() => deleteKnowledgeItem(it.id), "Deleted.");
                    }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
