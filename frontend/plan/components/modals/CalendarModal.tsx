import React, { useEffect, useState } from "react";
import { toast } from "react-toastify";
import styled from "styled-components";

interface RowProps {
    $align?: "flex-start" | "flex-end" | "center" | "baseline" | "stretch";
}

const Row = styled.div<RowProps>`
    display: flex;
    width: 100%;
    gap: 10px;
    align-items: center;
    justify-content: center;
`;

const Outer = styled.div`
    overflow-x: hidden;
`;

const Link = styled.div`
    display: flex;
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

const Button = styled.a`
    border-radius: 12px;
    display: block;
    background-color: #209cee;
    border-color: transparent;
    color: #fff;
    padding: 5px 15px;
    font-size: 0.75em;
    width: 100%
    text-align: center
`;

interface CalendarModalProps {
    $schedulePk: number;
}

const CalendarModal = ({ $schedulePk: schedulePk }: CalendarModalProps) => {
    const [url, setUrl] = useState<string>("INVALID");

    console.log(schedulePk);
    useEffect(() => {
        setUrl(`http://localhost:8000/api/plan/${schedulePk}/calendar/`);
    }, []);

    return (
        <Outer>
            <BigText>
                You can use the button below to download your schedule as an ICS
                file which you can import into a Google or macOS Calendar. This
                calendar will display all your classes and class times until the
                end of the semester.
                <br />
                <br />
                This file is personalized for your account, don't share it with
                others.
                <br />
                <br />
            </BigText>
            <Row>
                <Button href={url} download="plan.ics">
                    Download
                </Button>
            </Row>

            <hr />

            <Row className="columns has-text-centered">
                <div className="column">
                    <h3>
                        <b>Import to Google Calendar</b>
                    </h3>
                    <BigText>
                        Import the downloaded file to Google Calendar app. Need
                        help?
                        <br />
                        <a
                            href="https://support.google.com/calendar/answer/37118?sjid=16812697295393986554-NA&visit_id=638928653078159420-327839679&rd=1"
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
                        Import the downloaded file to the macOS Calendar app.
                        Need help?
                        <br />
                        <a
                            href="https://support.apple.com/guide/calendar/import-or-export-calendars-icl1023/15.0/mac/15.0"
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
