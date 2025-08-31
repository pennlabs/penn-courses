import React, { useEffect, useState } from "react";
import { toast } from "react-toastify";
import styled from "styled-components";

interface RowProps {
    $align?: "flex-start" | "flex-end" | "center" | "baseline" | "stretch";
}

const Row = styled.div<RowProps>`
    display: flex;
    flex-wrap: wrap;
    align-items: ${(props) => props.$align || "stretch"};
`;

const Outer = styled.div`
    overflow-x: hidden;
`;

const Link = styled.div`
    display: flex;
    width: 100%;
    gap: 10px;
    align-items: center;
    justify-content: center;
`;

const LoveFromLabs = styled.div`
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    font-size: 0.75rem;
`;

const BigText = styled.p`
    margin: 10px 0;
    font-size: 14px;
    line-height: 1.5;
`;

const Button = styled.button`
    border-radius: 10px;
    display: block;
    background-color: #209cee;
    border-color: transparent;
    color: #fff;
    padding: 5px 10px;
`;

interface CalendarModalProps {
    $schedulePk: number;
}

const CalendarModal = ({ $schedulePk: schedulePk }: CalendarModalProps) => {
    const [url, setUrl] = useState<string>("INVALID");

    console.log(schedulePk)
    useEffect(() => {
        setUrl(`http://penncourseplan.com/api/plan/${schedulePk}/calendar`);
    }, []);

    return (
        <Outer>
            <BigText>
                You can use the ICS URL below to import your schedule into a
                Google or macOS Calendar. This calendar will display all your
                classes and class times until the end of the semester.
                <br />
                <br />
                This link is personalized for your account, don't share it with
                others.
            </BigText>
            <Row $align="center" className="row field has-addons is-expanded">
                <Link>
                    <input
                        type="text"
                        readOnly
                        value={url}
                        onClick={(e) => (e.target as HTMLInputElement).select()}
                    />
                    <Button
                        onClick={async () => {
                            try {
                                await navigator.clipboard.writeText(url);
                                toast.info("Copied to clipboard!");
                            } catch (error) {
                                toast.error(
                                    "Failed to copy! You need to manually copy the URL."
                                );
                            }
                        }}
                    >
                        Copy
                    </Button>
                </Link>
            </Row>

            <hr />

            <Row className="columns has-text-centered">
                <div className="column">
                    <h3>
                        <b>Import to Google Calendar</b>
                    </h3>
                    <BigText>
                        Use the URL above to import to Google Calendar. Need
                        help?
                        <br />
                        <a
                            href="https://support.google.com/calendar/answer/37100#add_via_link"
                            target="_blank"
                            rel="noreferrer noopener"
                        >
                            Check out this guide!
                        </a>
                    </BigText>
                </div>
                <div className="column">
                    <h3>
                        <b>Import to macOS Calendar</b>
                    </h3>
                    <BigText>
                        Use the URL above to import to the macOS Calendar app.
                        Need help?
                        <br />
                        <a
                            href="https://support.apple.com/guide/calendar/subscribe-to-calendars-icl1022/mac"
                            target="_blank"
                            rel="noreferrer noopener"
                        >
                            Check out this guide!
                        </a>
                    </BigText>
                </div>
            </Row>
            <LoveFromLabs>
                With <i className="fa fa-heart" style={{ color: "red" }} />
                <a
                    href="//pennlabs.org"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Penn Labs
                </a>
            </LoveFromLabs>
        </Outer>
    );
};

export default CalendarModal;
