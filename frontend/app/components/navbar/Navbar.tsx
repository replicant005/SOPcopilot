"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { Bars3Icon } from "@heroicons/react/24/solid";

export default function Navbar() {
  const pathname = usePathname();

  function linkStyle(href: string) {
    const base = "transition-colors duration-200";
    const active = "text-[#2263af] font-semibold";
    const inactive = "text-black hover:text-[#2263af]";
  
    return `${base} ${pathname === href ? active : inactive}`;
  }

  return (
    <nav className="fixed top-0 left-0 right-0 z-30 py-6 px-6 bg-[F2EEEB]">
      <div className="flex justify-between items-center w-full max-w-[98%] mx-auto">
        <Link href="/">
          <Image
            src="/lightbulb_icon.svg"
            alt="Logo"
            width={50}
            height={50}
            priority
          />
        </Link>


        <div className="hidden md:flex gap-8 text-sm">
          <Link href="/" className={linkStyle("/")}>
            dashboard
          </Link>
          <Link href="/FAQ" className={linkStyle("/FAQ")}>
            FAQ
          </Link>
          <Link href="/notepad" className={linkStyle("/notepad")}>
            notepad
          </Link>
        </div>

        <div className="md:hidden flex justify-end">
          <Bars3Icon className="h-6 w-6 text-[#ff6600]" />
        </div>
      </div>
    </nav>
  );
}
