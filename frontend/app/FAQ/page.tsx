"use client";
import Image from "next/image";
import { useEffect, useRef } from "react";

export default function FAQ() {
    const pacmanRef = useRef<HTMLImageElement>(null);


    useEffect(() => {
        let ticking = false;
      
        const onScroll = () => {
          if (!ticking) {
            window.requestAnimationFrame(() => {
              const y = window.scrollY;
              pacmanRef.current!.style.transform = `translateY(${y * 0.25}px)`;
              ticking = false;
            });
            ticking = true;
          }
        };

        window.addEventListener("scroll", onScroll, { passive: true });
        return () => window.removeEventListener("scroll", onScroll);
      }, []);


    return (
        <div
            className="relative flex items-center justify-center min-h-screen bg-no-repeat bg-cover px-6
            transform translate-x-0"
            style={{
                backgroundImage: `url('/Group 30.svg')`,
                backgroundSize: "100%",
                backgroundPosition: "center ",
            }}
        >
            <div ref={pacmanRef} className="absolute left-10 top-20">
            <Image
                src="/green.svg"
                alt="Green line decor"
                width={1300}
                height={1100}
            />
            </div>
        
            {/* Content Box */}
            <div className="mt-10 ml-40 flex items-start gap-20 max-w-[1000px]">

            {/* Text Content */}
            <div className="max-w-[800px]">
            <p className="text-gray-700 mt-4 text-left text-[19px]">
                <strong>Why did we create Squill?</strong>
            </p>

            <p className="text-gray-700 mt-4 text-left text-[19px]">
                We created Squill after noticing a significant disconnect between students and available scholarship opportunities.
                Each year, over $100 million in U.S. scholarships goes unclaimed due to a lack of applicants (Forbes).
                Squill bridges this gap by making the application process clearer, more accessible, and easier to navigate.
            </p>

            <p className="text-gray-700 mt-4 text-left text-[19px]">
                <strong>How do I use Squill?</strong>
            </p>

            <p className="text-gray-700 mt-4 text-left text-[19px]">
                Squill is designed to help you write Statements of Purpose for applications ranging from graduate school to scholarships.
                Start by clicking on <strong>notepad</strong> in the top left of the page, then follow the guided prompts.
            </p>
            </div>

            {/* Start Now Button */}
            {/* <Link href="/notepad">
            <button className="whitespace-nowrap rounded-full bg-green-600 px-8 py-4 text-white text-lg font-semibold
                                hover:bg-green-700 transition-colors self-start">
                Start Now
            </button>
            </Link> */}

            </div>
            </div>
    );
}
