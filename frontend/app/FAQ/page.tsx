"use client";
import Image from "next/image";

export default function ThoughtMirror() {
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

            {/* Content Box */}
            <div className="absolute bg-transparent bg-opacity-80 p-10 rounded-lg max-w-3xl text-center">
                <Image
                    src="/Group 13.svg"
                    alt="taketime-text"
                    width={600}
                    height={800}
                    className="absolute right-34 bottom-40 rotate-0 transform translate-x-100"
                />

                <div className="transform translate-y-40 translate-x-40 mx-auto" style={{ minWidth: "800px" }}>
                    <p className="text-xs text-gray-700 mt-4 text-right" style={{fontSize: "19px"}}>
                        <strong>XXX</strong> meowmeoewmeowmeow
                    </p>
                    <p className="text-xs text-gray-700 mt-4 text-right" style={{fontSize: "19px"}}>
                        Meow meow meow moew? meow meow...
                    </p>
                    <p className="text-xs text-gray-700 mt-4 text-right" style={{fontSize: "19px"}}>
                        Start writing your true self today. meow
                    </p>
                </div>
            </div>
        </div>
    );
}
