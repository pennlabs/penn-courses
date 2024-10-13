import React from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import Image from "next/image";

export default function About() {
    return (
        <div className={cn("mx-[20%]")}>
            <h2>Hey there!</h2>
            <p>Welcome to the new Penn Course Review!</p>
            <p>
                The student-run Penn Course Review has served as a valuable
                guide for course selection since the 1960s. In 2014, Penn Course
                Review was completely redesigned to simplify the search
                experience. In 2018, we updated the site again to continue
                providing you with the best insights on courses. In 2021, we
                migrated the site over to a shared backend with{" "}
                <a
                    target="_blank"
                    rel="noopener noreferrer"
                    href="https://penncoursealert.com/"
                >
                    Penn Course Alert
                </a>{" "}
                and{" "}
                <a
                    target="_blank"
                    rel="noopener noreferrer"
                    href="https://penncourseplan.com/"
                >
                    Penn Course Plan
                </a>
                , allowing us to serve additional metrics about course
                registration difficulty (based on Penn Course Alert usage data
                and course status updates). We hope to continue updating and
                improving Penn Course Review in the years to come!
            </p>

            <h2>About</h2>
            <p>
                Penn Course Review is a student-run service that provides
                numerical ratings and metrics for undergraduate courses and
                professors at the University of Pennsylvania. PCR has a long
                history of being a valuable and influential guide for course
                selection.
            </p>
            <p>
                PCR is developed and managed by{" "}
                <a
                    target="_blank"
                    rel="noopener noreferrer"
                    href="https://pennlabs.org/"
                >
                    Penn Labs
                </a>
                , a student developer organization on Penn&apos;s campus.
            </p>

            <p>
                Penn Course Review compiles its information from online course
                evaluations conducted at the end of each semester by the
                Provost&apos;s office in conjunction with ISC.
            </p>
            <p>
                Your evaluations and comments feed the Review, so the more
                information you provide about your courses and professors, the
                more comprehensive Penn Course Review will be.
            </p>

            <p>
                If you want to look at courses on the go,{" "}
                <a
                    target="_blank"
                    rel="noopener noreferrer"
                    href="https://pennlabs.org/mobile/"
                >
                    PennMobile
                </a>{" "}
                is available for download! In the courses section, you are able
                to view course descriptions and ratings!
            </p>
            <p>
                Interested in building something using the Penn Courses API?
                Check our our{" "}
                <a
                    target="_blank"
                    rel="noopener noreferrer"
                    href="https://penncoursereview.com/api/documentation/"
                >
                    API documentation
                </a>
                .
            </p>
            <p>Thanks and happy searching,</p>
            <p>
                <strong>Penn Labs</strong>
            </p>

            <Image
                alt="Penn Labs"
                src="/static/image/labs.png"
                width={100}
                height={100}
            />

            <h2>Questions</h2>
            <p>
                If you have any questions, take a look at our{" "}
                <Link href="/faq">FAQs</Link> section.
            </p>
        </div>
    );
}
