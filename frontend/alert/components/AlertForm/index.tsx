import React, { useEffect, useState, useRef } from "react";
import PropTypes from "prop-types";
import styled from "styled-components";
import * as Sentry from "@sentry/browser";

import { parsePhoneNumberFromString } from "libphonenumber-js/min";

import { Center } from "pcx-shared-components/src/common/layout";
import { Input } from "../Input";
import AutoComplete from "../AutoComplete";
import getCsrf from "../../csrf";
import { User, Section } from "../../types";

const SubmitButton = styled.button`
    border-radius: 5px;
    background-color: #209cee;
    color: white;
    font-size: 1em;
    margin: 1em;
    width: 5em;
    padding: 0.7em 1em;
    transition: 0.2s all;
    border: none;
    cursor: pointer;
    :hover {
        background-color: #1496ed;
    }
`;

const AlertText = styled.div`
    padding-top: 1rem;
    color: #555555;
`;

const ClosedText = styled.div`
    padding-top: 0.5rem;
    color: #555555;
    align-items: center;
    justify-content: center;
`;

const Form = styled.form`
    display: flex;
    flex-direction: column;
`;


const spacer = {
    container: {
      width: "auto",
      height: "auto",
      marginLeft: "0.25rem",
    },
  } as const;

interface RadioSetProps {
    selected: string;
    options: { label: string; value: string }[];
    setSelected: (val: string) => void;
}

const RadioSet = ({ selected, options, setSelected }: RadioSetProps) => (
    <span>
        {options.map(({ label, value }) => (
            <>
                <label htmlFor={value} style={spacer.container}>
                    <input
                        type="radio"
                        name="name"
                        id={value}
                        value={value}
                        onChange={(e) => setSelected(e.target.value)}
                        checked={value === selected}
                    />
                    {label}
                </label>
            </>
        ))}
    </span>
);

RadioSet.propTypes = {
    selected: PropTypes.string,
    options: PropTypes.arrayOf(PropTypes.string),
    setSelected: PropTypes.func,
};

const doAPIRequest = (
    url: string,
    method: string = "GET",
    body: any = {},
    extraHeaders: Record<string, string> = {}
) =>
    fetch(url, {
        method,
        credentials: "include",
        mode: "same-origin",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrf(),
            ...extraHeaders,
        },
        body: JSON.stringify(body),
    });

interface AlertFormProps {
    user: User;
    setResponse: (res: Response) => void;
    setTimeline: React.Dispatch<React.SetStateAction<string | null>>;
    autofillSection?: string;
}

const AlertForm = ({
    user,
    setResponse,
    setTimeline,
    autofillSection = "",
}: AlertFormProps) => {
    const [selectedCourses, setSelectedCourses] = useState<Set<Section>>(
        new Set()
    );

    const [email, setEmail] = useState("");

    const [phone, setPhone] = useState("");
    const [isPhoneDirty, setPhoneDirty] = useState(false);

    const [autoResub, setAutoResub] = useState("false");
    const [closedNotif, setClosedNotif] = useState(false);

    const autoCompleteInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        const phonenumber =
            user && parsePhoneNumberFromString(user.profile.phone || "");
        setPhone(
            phonenumber
                ? phonenumber.formatNational()
                : (user && user.profile.phone) || ""
        );
        setEmail((user && user.profile.email) || "");
    }, [user]);

    const contactInfoChanged = () =>
        !user || user.profile.email !== email || isPhoneDirty;

    const sendError = (status, message) => {
        const blob = new Blob([JSON.stringify({ message })], {
            type: "application/json",
        });
        setResponse(new Response(blob, { status }));
    };

    const handleError = (e) => {
        Sentry.captureException(e);
        sendError(
            500,
            "We're sorry, but there was an error sending your request to our servers. Please try again!"
        );
    };

    // Clear all sections the user selected
    const clearSelections = () => {
        setSelectedCourses(new Set());
    };

    const deselectCourse = (section: Section): boolean => {
        const newSelectedCourses = new Set(selectedCourses);
        const removed = newSelectedCourses.delete(section);
        removed && setSelectedCourses(newSelectedCourses);
        return removed;
    }

    const submitRegistration = () => {
        // if user has a auto fill section and didn't change the input value then register for section
        if (
            autoCompleteInputRef.current &&
            autoCompleteInputRef.current.value === autofillSection
        ) {
            doAPIRequest("/api/alert/registrations/", "POST", {
                section: autofillSection,
                auto_resubscribe: autoResub === "true",
                // close_notification: closedNotif,
            })
                .then(setResponse)
                .catch(handleError);
        }

        // register all selected sections
        const promises: Array<Promise<Response>> = [];
        selectedCourses.forEach((section) => {
            const promise = doAPIRequest("/api/alert/registrations/", "POST", {
                section: section.section_id,
                auto_resubscribe: autoResub === "true",
                // close_notification: closedNotif,
            });
            promises.push(promise);
        });

        const sections = Array.from(selectedCourses)

        Promise.allSettled(promises)
            .then((responses) => responses.forEach(
                (res: PromiseSettledResult<Response>, i) => {
                    if (res.status === "fulfilled") {
                        console.log("fulfilled")
                        setResponse(res.value);
                        deselectCourse(sections[i]);
                    } else {
                        handleError(res.reason);
                    }
                }));
    };

    const onSubmit = () => {
        if (phone.length === 0 && email.length === 0) {
            sendError(
                400,
                "Please add at least one contact method (either email or phone number)."
            );
            return;
        }
        if (phone.length !== 0 && !parsePhoneNumberFromString(phone, "US")) {
            sendError(
                400,
                "Please enter a valid phone US # (or leave the field blank)."
            );
            return;
        }

        if (contactInfoChanged()) {
            doAPIRequest("/accounts/me/", "PATCH", {
                profile: { email, phone },
            })
                .then((res) => {
                    if (!res.ok) {
                        throw new Error(JSON.stringify(res));
                    } else {
                        return submitRegistration();
                    }
                })
                .catch(handleError);
        } else {
            submitRegistration();
        }
    };

    return (
        <Form>
            <AutoComplete
                defaultValue={autofillSection}
                selectedCourses={selectedCourses}
                setSelectedCourses={setSelectedCourses}
                setTimeline={setTimeline}
                inputRef={autoCompleteInputRef}
                clearSelections={clearSelections}
            />
            <Input
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
            />
            <Input
                placeholder="Phone"
                value={phone}
                onChange={(e) => {
                    setPhone(e.target.value);
                    setPhoneDirty(true);
                }}
            />
            <Center>
                <AlertText>
                    Alert me
                    <RadioSet
                        options={[
                            { label: "once", value: "false" },
                            { label: "until I cancel", value: "true" },
                        ]}
                        setSelected={setAutoResub}
                        selected={autoResub}
                    />
                </AlertText>
{/* 
                <ClosedText>
                    Closed Notification?
                    <Input
                        type="checkbox"
                        checked={closedNotif}
                        onChange={(e) => {
                            setClosedNotif(e.target.checked);
                        }}
                        style={spacer.container}
                    />
                </ClosedText> */}

                <SubmitButton
                    onClick={(e) => {
                        e.preventDefault();
                        onSubmit();
                    }}
                >
                    Submit
                </SubmitButton>
            </Center>
        </Form>
    );
};

export default AlertForm;
