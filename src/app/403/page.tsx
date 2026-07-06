"use client";

import { useRouter } from "next/navigation";
import { ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/components/layout/AuthProvider";
import { ROLE_HOME } from "@/lib/auth/roles";

export default function ForbiddenPage() {
  const router = useRouter();
  const { user } = useAuth();

  return (
    <div className="flex min-h-[70vh] items-center justify-center p-4">
      <Card className="w-full max-w-md text-center">
        <CardHeader className="items-center">
          <ShieldAlert className="mx-auto mb-2 h-12 w-12 text-destructive" />
          <CardTitle>Access denied</CardTitle>
          <CardDescription>
            Your {user ? `“${user.role}” ` : ""}account doesn&apos;t have permission to view
            this page.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            className="w-full"
            onClick={() => router.replace(user ? ROLE_HOME[user.role] : "/login")}
          >
            Go to my workspace
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
