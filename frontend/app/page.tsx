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
    
            bannerRef.current!.style.transform = `translateY(${y * 0.15}px)`;
            pacmanRef.current!.style.transform = `translateY(${y * 0.45}px)`;
            heroRef.current!.style.transform = `translateY(${y * 0.1}px)`;
            subtitleRef.current!.style.transform = `translateY(${y * 0.12}px)`;
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


            <Image
              ref={pacmanRef}
              src="/pencil1.png"
              alt="pencil icon"
              width={90}
              height={100}
              className="absolute left-35 top-35 z-20 will-change-transform"
            />


            {/* HERO TEXT that doesnt move */}
            <div
              ref={heroRef}
              className="absolute left-65 top-34 z-20 max-w-xl"
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
              className="absolute left-65 top-75 z-20"
              style={{ transform: `translateY(${scrollY * 0.12}px)` }}
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
                About Squill:
              </h2>
            </div>


            {/* ABOUT BODY TEXT */}
            <div
              // ref={aboutPara}
              className="absolute left-70 top-270 max-w-md z-20"
              // style={{ transform: `translateY(${scrollY * 0.18}px)` }}
            >
              <p className="text-base md:text-lg leading-relaxed text-[#3071D2]">
              Lorem Ipsum is simply dummy text of the printing and typesetting industry.
               Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, 
               when an unknown printer took a galley of type and scrambled it to make a type 
               specimen book. It has survived not only five centuries, but also the leap into 
               electronic typesetting, remaining essentially unchanged. It was popularised in 
               the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, 
               and more recently with desktop publishing software like Aldus PageMaker including 
               versions of Lorem Ipsum.
              </p>
            </div>


            <Image
              src="/example.png"
              alt="banner"
              width={600}
              height={600}
              priority
              className="absolute left-190 top-290 z-10 will-change-transform"
            />


            {/* <div className="text-left absolute left-65 top-255 max-w-5xl">
                <p className="text-sm " style={{color: "#3071D2"}}>

                    hello test
                </p>

            </div> */}


            {/* LOWER IMAGE (medium speed) */}
            <Image
              ref={lowerRef}
              src="/lower.svg"
              alt="lower"
              width={1300}
              height={1000}
              className="absolute left-50 top-340 z-10 will-change-transform"
            />

        </div>
    );
}