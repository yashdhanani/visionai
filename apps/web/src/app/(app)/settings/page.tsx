"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { useAuthStore } from "@/store/auth";
import { useTheme } from "next-themes";
import { useToast } from "@/components/ui/toast";
import { api } from "@/lib/api";
import { User, Shield, Palette, Key, Save } from "lucide-react";

export default function SettingsPage() {
  const { user, setAuth, token } = useAuthStore();
  const { theme, setTheme } = useTheme();
  const { success, error: toastError } = useToast();
  const [name, setName] = useState(user?.name || "");
  const [currentPw, setCurrentPw] = useState("");
  const [newPw, setNewPw] = useState("");
  const [loading, setLoading] = useState(false);
  const [mounted, setMounted] = useState(false);

  const [apiKeys, setApiKeys] = useState<any[]>([]);
  const [loadingKeys, setLoadingKeys] = useState(false);
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [createdKeySecret, setCreatedKeySecret] = useState<string | null>(null);

  const fetchApiKeys = async () => {
    setLoadingKeys(true);
    try {
      const res = await api.get("/api/v1/auth/api-keys");
      setApiKeys(res.data.data || []);
    } catch {
      // ignore
    } finally {
      setLoadingKeys(false);
    }
  };

  useEffect(() => {
    setMounted(true);
    fetchApiKeys();
  }, []);

  const handleCreateKey = async () => {
    if (!newKeyName.trim()) return;
    try {
      const res = await api.post("/api/v1/auth/api-keys", { name: newKeyName.trim() });
      if (res.data.data?.key) {
        setCreatedKeySecret(res.data.data.key);
      }
      success("API Key created successfully!");
      setNewKeyName("");
      setShowKeyModal(false);
      fetchApiKeys();
    } catch (err: any) {
      toastError(err.response?.data?.error?.message || "Failed to create API key");
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    if (!confirm("Are you sure you want to revoke this API key? Any application using it will lose access.")) return;
    try {
      await api.delete(`/api/v1/auth/api-keys/${keyId}`);
      success("API key revoked");
      fetchApiKeys();
    } catch (err: any) {
      toastError(err.response?.data?.error?.message || "Failed to revoke key");
    }
  };

  const handleSaveProfile = async () => {
    setLoading(true);
    try {
      success("Profile saved (name update coming soon)");
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async () => {
    if (!currentPw || !newPw) return;
    setLoading(true);
    try {
      await api.post("/api/v1/auth/change-password", { current_password: currentPw, new_password: newPw });
      success("Password changed. Please login again.");
      setCurrentPw("");
      setNewPw("");
    } catch (err: any) {
      toastError(err.response?.data?.error?.message || "Failed to change password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-sm text-zinc-500 mt-1">Manage your account and preferences</p>
      </div>

      {/* Account */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <User className="h-4 w-4" />
            <CardTitle className="text-sm">Account</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-1 block">Name</label>
            <Input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">Email</label>
            <Input value={user?.email || ""} disabled />
            <p className="text-xs text-zinc-500 mt-1">Email cannot be changed</p>
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">Role</label>
            <Input value={user?.role || ""} disabled />
          </div>
          <Button onClick={handleSaveProfile} loading={loading}><Save className="h-4 w-4 mr-1" /> Save Changes</Button>
        </CardContent>
      </Card>

      {/* Security */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4" />
            <CardTitle className="text-sm">Change Password</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-1 block">Current Password</label>
            <Input type="password" value={currentPw} onChange={(e) => setCurrentPw(e.target.value)} />
          </div>
          <div>
            <label className="text-sm font-medium mb-1 block">New Password</label>
            <Input type="password" value={newPw} onChange={(e) => setNewPw(e.target.value)} />
          </div>
          <Button onClick={handleChangePassword} disabled={!currentPw || !newPw} loading={loading}>
            Change Password
          </Button>
        </CardContent>
      </Card>

      {/* Appearance */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Palette className="h-4 w-4" />
            <CardTitle className="text-sm">Appearance</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <Switch checked={mounted && theme === "dark"} onCheckedChange={(v) => setTheme(v ? "dark" : "light")} label="Dark Mode" />
        </CardContent>
      </Card>

      {/* API Keys */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Key className="h-4 w-4" />
              <CardTitle className="text-sm">API Keys</CardTitle>
            </div>
            <Button size="sm" onClick={() => setShowKeyModal(true)}>+ Generate New Key</Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-zinc-500">
            Use API keys to connect VisionAI into any web, mobile, desktop app, or Python script.
          </p>

          {createdKeySecret && (
            <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-700 dark:text-emerald-300 space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wider">Your New API Key (Copy now — it won&apos;t be shown again):</p>
              <div className="flex items-center gap-2">
                <code className="flex-1 p-2 rounded bg-white dark:bg-zinc-950 font-mono text-xs border select-all">{createdKeySecret}</code>
                <Button size="sm" variant="outline" onClick={() => {
                  navigator.clipboard.writeText(createdKeySecret);
                  success("API Key copied to clipboard!");
                }}>
                  Copy
                </Button>
              </div>
            </div>
          )}

          {loadingKeys ? (
            <div className="text-sm text-zinc-400">Loading API keys...</div>
          ) : apiKeys.length === 0 ? (
            <div className="text-sm text-zinc-500 py-2">No active API keys. Click &quot;Generate New Key&quot; to create one.</div>
          ) : (
            <div className="divide-y divide-border border rounded-lg">
              {apiKeys.map((k: any) => (
                <div key={k.id} className="p-3 flex items-center justify-between text-sm">
                  <div>
                    <p className="font-medium">{k.name}</p>
                    <p className="text-xs font-mono text-zinc-500">{k.prefix_display}... • Created {new Date(k.created_at).toLocaleDateString()}</p>
                  </div>
                  <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/50" onClick={() => handleRevokeKey(k.id)}>
                    Revoke
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* New Key Modal */}
      {showKeyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-card border border-border rounded-xl p-6 w-full max-w-md space-y-4 shadow-xl">
            <h3 className="text-lg font-bold">Generate API Key</h3>
            <p className="text-sm text-zinc-500">Provide a name to identify this key (e.g. Mobile App, Backend Service, Script).</p>
            <Input
              placeholder="e.g., My Python Automation"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              autoFocus
            />
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setShowKeyModal(false)}>Cancel</Button>
              <Button onClick={handleCreateKey} disabled={!newKeyName.trim()}>Generate Key</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}