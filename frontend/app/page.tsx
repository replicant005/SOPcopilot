"use client";
import Image from "next/image";
import { useEffect, useRef } from "react";



export default function Homepage() {

    const bannerRef = useRef<HTMLImageElement>(null);
    const pacmanRef = useRef<HTMLImageElement>(null);
    const heroRef = useRef<HTMLDivElement>(null);
    const subtitleRef = useRef<HTMLDivElement>(null);
    const aboutRef = useRef<HTMLDivElement>(null);
    // const aboutPara = useRef<HTMLImageElement>(null);
    const lowerRef = useRef<HTMLImageElement>(null);
  

    useEffect(() => {
      let ticking = false;
    
      const onScroll = () => {
        if (!ticking) {
          window.requestAnimationFrame(() => {
            const y = window.scrollY;
    
            bannerRef.current!.style.transform = `translateY(${y * 0.2}px)`;
            pacmanRef.current!.style.transform = `translateY(${y * 0.45}px)`;
            heroRef.current!.style.transform = `translateY(${y * 0.10}px)`;
            subtitleRef.current!.style.transform = `translateY(${y * 0.2}px)`;
            aboutRef.current!.style.transform = `translateY(${y * 0.18}px)`;
            // aboutPara.current!.style.transform = `translateY(${y * 0.18}px)`;
            lowerRef.current!.style.transform = `translateY(${y * 0.3}px)`;
    
            ticking = false;
          });
          ticking = true;
        }
      };
    
      window.addEventListener("scroll", onScroll, { passive: true });
      return () => window.removeEventListener("scroll", onScroll);
    }, []);
    

    return (

        <div className="relative flex items-center justify-center min-h-screen px-6">

            <Image
              ref={bannerRef}
              src="/lightbulb_banner3.png"
              alt="banner"
              width={3400}
              height={1500}
              priority
              className="absolute left-0 top-7 z-10 will-change-transform"
            />

            <div ref={pacmanRef} className="absolute left-51 top-40 z-20 will-change-transform opacity-35">
            <Image
              src="/small_stick.png"
              alt="pencil icon"
              width={15}
              height={10}
            />
            </div>


            {/* HERO TEXT that doesnt move */}
            <div
              ref={heroRef}
              className="absolute left-60 top-34 z-20 max-w-xl"
              style={{ transform: `translateY(${scrollY * 0.1}px)` }}
            >
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-light leading-tight">
                welcome to <span className="font-semibold text-black"></span>
              </h1>
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-semibold text-black leading-tight">
                Squill.
              </h1>
            </div>


            {/* SUBTITLE */}
            <div
              ref={subtitleRef}
              className="absolute left-60 top-75 z-20"
              style={{ transform: `translateY(${scrollY * 0.1}px)` }}
            >
              <h2 className="text-2xl md:text-3xl font-medium tracking-wide">
                write. create. explore.
              </h2>
            </div>


            {/* ABOUT HEADER */}
            <div
              ref={aboutRef}
              className="absolute left-65 top-210 z-20"
              style={{ transform: `translateY(${scrollY * 0.18}px)` }}
            >
              <h2 className="text-3xl md:text-4xl font-semibold">
                About Squill
              </h2>
            </div>


            {/* ABOUT BODY TEXT */}
            <div
              className="absolute left-70 top-270 max-w-md z-20"
            >
              <p className="text-base md:text-lg leading-relaxed text">
              Squill is a guided writing tool designed to help users develop authentic, 
              compelling Statements of Purpose. It collects a small amount of input, such 
              as scholarship or application details and a few key resume points, and uses 
              this information to generate thoughtful, personalized questions. Rather than 
              rewriting a user’s work, Squill prompts reflection and incremental storytelling, 
              helping users articulate their experiences, motivations, and growth step by step. 
              Over time, this process results in a substantial body of text that genuinely 
              reflects the user’s intellectual interests and personal identity.
              </p>
            </div>


            <Image
              src="/example1.png"
              alt="banner"
              width={410}
              height={600}
              priority
              className="absolute left-200 top-290 z-11 will-change-transform"
            />

            <Image
              src="/example2.png"
              alt="banner"
              width={410}
              height={600}
              priority
              className="absolute left-225 top-260 z-10 will-change-transform"
            />


            {/* LOWER IMAGE (medium speed) */}
            <Image
              ref={lowerRef}
              src="/blue_s.png"
              alt="blue squiggle banner"
              width={1300}
              height={1000}
              className="absolute left-50 top-290 z-10 will-change-transform"
            />

        </div>
    );
}