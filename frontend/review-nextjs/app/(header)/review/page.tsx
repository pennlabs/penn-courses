"use client";
import { useEffect, useState } from "react";

export default function TestJWT() {
    const [data, setData] = useState<any>(null);
    useEffect(() => {
        fetch("/api/review/testjwt")
            .then((res) => res.json())
            .then((data) => {
                setData(data);
                console.log("Profile Data:", data);
            });
    }, []);
    return (
        <div className="mx-[20%]">
            {/* <button onClick={handleClick}>Click if Authenticated</button> */}
        </div>
    );
}
