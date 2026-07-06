'use client';

import { useCallback, useEffect, useState, type FormEvent } from 'react';
import {
    Loader2, UserPlus, UserCog, ShieldCheck, Stethoscope, ClipboardList,
    CheckCircle2, XCircle, KeyRound,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
    Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import { useAuth } from '@/components/layout/AuthProvider';
import { ALL_ROLES, type Role } from '@/lib/auth/roles';

interface StaffUser {
    id: string;
    username: string;
    full_name: string;
    role: Role;
    is_active: boolean;
    created_at: string | null;
}

const ROLE_META: Record<Role, { label: string; icon: typeof ShieldCheck; badgeClass: string }> = {
    admin: { label: 'Admin', icon: ShieldCheck, badgeClass: 'bg-purple-100 text-purple-700 border-purple-200' },
    doctor: { label: 'Doctor', icon: Stethoscope, badgeClass: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
    receptionist: { label: 'Receptionist', icon: ClipboardList, badgeClass: 'bg-sky-100 text-sky-700 border-sky-200' },
};

export default function StaffManagementPage() {
    const { user: me } = useAuth();
    const [users, setUsers] = useState<StaffUser[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [busyUserId, setBusyUserId] = useState<string | null>(null);

    // Add-staff form
    const [showForm, setShowForm] = useState(false);
    const [newUsername, setNewUsername] = useState('');
    const [newFullName, setNewFullName] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [newRole, setNewRole] = useState<Role>('receptionist');
    const [creating, setCreating] = useState(false);
    const [formError, setFormError] = useState<string | null>(null);

    const loadUsers = useCallback(async () => {
        try {
            const res = await fetch('/api/staff', { cache: 'no-store' });
            if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail ?? 'Failed to load staff');
            const data = await res.json();
            setUsers(data.users ?? []);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load staff');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { loadUsers(); }, [loadUsers]);

    const patchUser = async (userId: string, patch: Partial<Pick<StaffUser, 'role' | 'is_active'>> & { password?: string }) => {
        setBusyUserId(userId);
        try {
            const res = await fetch(`/api/staff/${userId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(patch),
            });
            const data = await res.json().catch(() => null);
            if (!res.ok) {
                alert(data?.detail ?? 'Update failed');
                return;
            }
            setUsers((prev) => prev.map((u) => (u.id === userId ? data.user : u)));
        } finally {
            setBusyUserId(null);
        }
    };

    const handleResetPassword = (staff: StaffUser) => {
        const pw = window.prompt(`New password for ${staff.username} (min 6 chars):`);
        if (!pw) return;
        if (pw.length < 6) { alert('Password must be at least 6 characters.'); return; }
        patchUser(staff.id, { password: pw });
    };

    const handleCreate = async (e: FormEvent) => {
        e.preventDefault();
        setFormError(null);
        setCreating(true);
        try {
            const res = await fetch('/api/staff', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: newUsername.trim(),
                    full_name: newFullName.trim(),
                    password: newPassword,
                    role: newRole,
                }),
            });
            const data = await res.json().catch(() => null);
            if (!res.ok) {
                setFormError(data?.detail ?? 'Failed to create user');
                return;
            }
            setUsers((prev) => [...prev, data.user]);
            setShowForm(false);
            setNewUsername(''); setNewFullName(''); setNewPassword(''); setNewRole('receptionist');
        } finally {
            setCreating(false);
        }
    };

    return (
        <div className="max-w-5xl mx-auto space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <UserCog className="w-6 h-6 text-primary" /> Staff Management
                    </h1>
                    <p className="text-muted-foreground text-sm mt-1">
                        Create staff accounts, assign roles, and control access.
                    </p>
                </div>
                <Button onClick={() => setShowForm((s) => !s)}>
                    <UserPlus className="w-4 h-4" /> {showForm ? 'Cancel' : 'Add Staff'}
                </Button>
            </div>

            {showForm && (
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg">New staff account</CardTitle>
                        <CardDescription>The user signs in with these credentials and only sees pages allowed for their role.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleCreate} className="grid gap-4 sm:grid-cols-2">
                            <div className="space-y-2">
                                <Label htmlFor="new-username">Username</Label>
                                <Input id="new-username" required minLength={3} value={newUsername}
                                    onChange={(e) => setNewUsername(e.target.value)} placeholder="e.g. dr.sharma" />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="new-fullname">Full name</Label>
                                <Input id="new-fullname" value={newFullName}
                                    onChange={(e) => setNewFullName(e.target.value)} placeholder="Dr. A. Sharma" />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="new-password">Password</Label>
                                <Input id="new-password" type="password" required minLength={6} value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)} placeholder="min 6 characters" />
                            </div>
                            <div className="space-y-2">
                                <Label>Role</Label>
                                <Select value={newRole} onValueChange={(v) => setNewRole(v as Role)}>
                                    <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
                                    <SelectContent>
                                        {ALL_ROLES.map((r) => (
                                            <SelectItem key={r} value={r}>{ROLE_META[r].label}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            {formError && (
                                <p role="alert" className="text-sm font-medium text-destructive sm:col-span-2">{formError}</p>
                            )}
                            <div className="sm:col-span-2">
                                <Button type="submit" disabled={creating}>
                                    {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <UserPlus className="w-4 h-4" />}
                                    Create account
                                </Button>
                            </div>
                        </form>
                    </CardContent>
                </Card>
            )}

            <Card>
                <CardHeader>
                    <CardTitle className="text-lg">Staff accounts ({users.length})</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                    {loading ? (
                        <div className="flex justify-center py-10"><Loader2 className="w-6 h-6 animate-spin text-muted-foreground" /></div>
                    ) : error ? (
                        <p className="text-sm text-destructive py-4">{error}</p>
                    ) : users.map((staff) => {
                        const meta = ROLE_META[staff.role] ?? ROLE_META.receptionist;
                        const RoleIcon = meta.icon;
                        const isSelf = staff.id === me?.id;
                        const busy = busyUserId === staff.id;
                        return (
                            <div key={staff.id}
                                className={`flex flex-col sm:flex-row sm:items-center gap-3 rounded-xl border p-4 ${staff.is_active ? 'bg-card' : 'bg-muted/50 opacity-75'}`}>
                                <div className="flex items-center gap-3 flex-1 min-w-0">
                                    <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center shrink-0">
                                        <RoleIcon className="w-5 h-5 text-muted-foreground" />
                                    </div>
                                    <div className="min-w-0">
                                        <p className="font-medium truncate">
                                            {staff.full_name || staff.username}
                                            {isSelf && <span className="ml-2 text-xs text-muted-foreground">(you)</span>}
                                        </p>
                                        <p className="text-xs text-muted-foreground truncate">@{staff.username}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2 flex-wrap">
                                    <Badge variant="outline" className={meta.badgeClass}>{meta.label}</Badge>
                                    <Badge variant="outline" className={staff.is_active
                                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                        : 'bg-red-50 text-red-600 border-red-200'}>
                                        {staff.is_active ? 'Active' : 'Deactivated'}
                                    </Badge>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Select value={staff.role} disabled={isSelf || busy}
                                        onValueChange={(v) => patchUser(staff.id, { role: v as Role })}>
                                        <SelectTrigger className="w-36" size="sm"><SelectValue /></SelectTrigger>
                                        <SelectContent>
                                            {ALL_ROLES.map((r) => (
                                                <SelectItem key={r} value={r}>{ROLE_META[r].label}</SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                    <Button variant="outline" size="sm" disabled={busy} title="Reset password"
                                        onClick={() => handleResetPassword(staff)}>
                                        <KeyRound className="w-4 h-4" />
                                    </Button>
                                    <Button
                                        variant={staff.is_active ? 'destructive' : 'default'}
                                        size="sm"
                                        disabled={isSelf || busy}
                                        onClick={() => patchUser(staff.id, { is_active: !staff.is_active })}
                                    >
                                        {busy
                                            ? <Loader2 className="w-4 h-4 animate-spin" />
                                            : staff.is_active
                                                ? <><XCircle className="w-4 h-4" /> Deactivate</>
                                                : <><CheckCircle2 className="w-4 h-4" /> Activate</>}
                                    </Button>
                                </div>
                            </div>
                        );
                    })}
                </CardContent>
            </Card>
        </div>
    );
}
