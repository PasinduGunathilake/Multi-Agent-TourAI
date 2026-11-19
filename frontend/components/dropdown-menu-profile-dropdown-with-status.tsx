"use client";

/**
 * A profile menu whose avatar shows an online dot, with a Pro badge in the header.
 * Updated to fetch profile picture from email/avatar_url, with Billing & Account Settings removed.
 */
import React from "react";
import { LogOutIcon, UserIcon, ChevronUp } from "lucide-react";
import {
  Avatar,
  AvatarBadge,
  AvatarFallback,
  AvatarImage,
} from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/contexts/AuthContext";

export interface ProfileDropdownProps {
  showDetails?: boolean;
  className?: string;
}

export const DropdownMenuProfileDropdownWithStatus: React.FC<ProfileDropdownProps> = ({
  showDetails = false,
  className,
}) => {
  const { user, logout } = useAuth();

  if (!user) return null;

  const displayName = user.display_name || user.email?.split("@")[0] || "Traveler";
  const email = user.email || "";
  const initials = (user.display_name || user.email || "U")[0].toUpperCase();

  // Fetch avatar image based on user's profile picture or email-derived avatar service
  const avatarUrl =
    user.avatar_url ||
    (email
      ? `https://unavatar.io/${encodeURIComponent(email)}?fallback=https%3A%2F%2Fapi.dicebear.com%2F7.x%2Finitials%2Fsvg%3Fseed%3D${encodeURIComponent(displayName)}`
      : undefined);

  return (
    <DropdownMenu className={className}>
      <DropdownMenuTrigger asChild>
        {showDetails ? (
          <Button
            aria-label="Open account menu"
            variant="ghost"
            className="w-full flex items-center justify-between gap-2 px-2.5 py-2 h-auto rounded-xl bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.08] text-left transition-all"
          >
            <div className="flex items-center gap-2.5 min-w-0 flex-1">
              <Avatar className="h-8 w-8 shrink-0">
                <AvatarImage alt={`@${displayName}`} src={avatarUrl} />
                <AvatarFallback>{initials}</AvatarFallback>
                <AvatarBadge className="bg-emerald-400" />
              </Avatar>
              <div className="flex flex-col min-w-0 flex-1">
                <span
                  className="text-[11px] font-medium text-white truncate block w-full"
                  title={email}
                >
                  {email}
                </span>
                <span className="text-[9px] text-teal-400 font-mono">
                  Authenticated
                </span>
              </div>
            </div>
            <ChevronUp className="w-3.5 h-3.5 text-white/40 shrink-0 ml-1 transition-transform duration-200 group-aria-expanded:rotate-180 group-aria-expanded:text-teal-400" />
          </Button>
        ) : (
          <Button
            aria-label="Open account menu"
            pill
            size="icon-lg"
            variant="ghost"
            className="p-0 border border-white/10"
          >
            <Avatar className="h-9 w-9">
              <AvatarImage alt={`@${displayName}`} src={avatarUrl} />
              <AvatarFallback>{initials}</AvatarFallback>
              <AvatarBadge className="bg-emerald-400" />
            </Avatar>
          </Button>
        )}
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="start"
        side="top"
        className="w-full min-w-[230px] p-1.5 shadow-2xl"
      >
        <DropdownMenuGroup>
          <DropdownMenuLabel className="font-normal p-2.5">
            <div className="flex items-center gap-3">
              <Avatar className="h-11 w-11 shrink-0">
                <AvatarImage alt={`@${displayName}`} src={avatarUrl} />
                <AvatarFallback className="text-sm font-bold">
                  {initials}
                </AvatarFallback>
              </Avatar>
              <div className="flex flex-col min-w-0 flex-1">
                <p className="font-bold text-white text-sm leading-tight truncate">
                  {displayName}
                </p>
                <p className="text-white/50 text-xs leading-normal truncate w-full mt-0.5" title={email}>
                  {email}
                </p>
                <Badge className="w-fit mt-1.5 text-[10px] px-1.5 py-0.5 leading-none" variant="teal">
                  Authenticated
                </Badge>
              </div>
            </div>
          </DropdownMenuLabel>

          <DropdownMenuSeparator />

          <DropdownMenuItem className="gap-2.5 px-3 py-2 cursor-pointer">
            <UserIcon className="w-4 h-4 text-teal-400 shrink-0" aria-hidden="true" />
            <span className="text-xs font-medium">View Profile</span>
          </DropdownMenuItem>
        </DropdownMenuGroup>

        <DropdownMenuSeparator />

        <DropdownMenuItem
          variant="destructive"
          onClick={() => logout()}
          className="gap-2.5 px-3 py-2 cursor-pointer"
        >
          <LogOutIcon className="w-4 h-4 text-rose-400 shrink-0" aria-hidden="true" />
          <span className="text-xs font-medium">Log out</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default DropdownMenuProfileDropdownWithStatus;
