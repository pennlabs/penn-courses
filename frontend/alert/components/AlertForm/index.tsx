import React, { useEffect, useState, useRef } from "react";
import styled from "styled-components";
import * as Sentry from "@sentry/browser";

import InfoTool from "pcx-shared-components/src/common/InfoTool";

import { isValidNumber, parsePhoneNumberFromString } from "libphonenumber-js";

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

const ClosedText = styled.div`
    padding-top: 0.5rem;
    color: #555555;
    align-items: center;
    justify-content: center;
    display: flex;
    flex-direction: row;
`;

const Form = styled.form`
    display: flex;
    flex-direction: column;
`;

const ClosedCheckbox = styled.input`
    width: auto;
    height: auto;
    margin-left: 0.5rem;
`;

const closeNotifInfoText = `Check this box to receive a
follow-up email when a course
closes again after alerting you
of an opening. Please note that
text notifications for course
closures are not currently
supported.`;

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
    sendError: (status: number, message: string) => void;
    setResponse: (res: Response) => void;
    setTimeline: React.Dispatch<React.SetStateAction<string | null>>;
    autofillSection?: string;
}

const AlertForm = ({
    user,
    sendError,
    setResponse,
    setTimeline,
    autofillSection = "",
}: AlertFormProps) => {
    const [selectedCourses, setSelectedCourses] = useState<Set<Section>>(
        new Set()
    );
    const [value, setValue] = useState(autofillSection);
    const [email, setEmail] = useState("");
    const [phone, setPhone] = useState("");
    const [isPhoneDirty, setPhoneDirty] = useState(false);
    const [closedNotif, setClosedNotif] = useState(false);
    const autoCompleteInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        const parsedNumber = user && parsePhoneNumberFromString(user.profile.phone || "", "US");
        setPhone(
            parsedNumber
                ? parsedNumber.formatNational()
                : (user && user.profile.phone) || ""
        );
        setEmail((user && user.profile.email) || "");
    }, [user]);

    const contactInfoChanged = () =>
        !user || user.profile.email !== email || isPhoneDirty;

    const isCourseOpen = (section) => {
        return fetch(`/api/base/current/sections/${section}/`)
            .then((res) =>
                res.json().then((courseResult) => {
                    const isOpen = courseResult["status"] === "O";
                    if (isOpen) {
                        setResponse(
                            new Response(
                                new Blob(
                                    [
                                        JSON.stringify({
                                            message:
                                                "Course is currently open!",
                                            status: 400,
                                        }),
                                    ],
                                    {
                                        type: "application/json",
                                    }
                                )
                            )
                        );
                    }

                    return isOpen;
                })
            )
            .catch((err) => {
                handleError(err);
                return false;
            });
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

    /**
     * Clear the input value and setValue
     * @param newSelectedCourses - most up-to-date selected courses set
     * @param suggestion - the section
     */
    const clearInputValue = () => {
        if (autoCompleteInputRef.current) {
            autoCompleteInputRef.current.value = "";
            setValue("");
        }
    };

    const deselectCourse = (section: Section): boolean => {
        const newSelectedCourses = new Set(selectedCourses);
        const removed = newSelectedCourses.delete(section);
        removed && setSelectedCourses(newSelectedCourses);

        if (newSelectedCourses.size === 0) {
            clearInputValue();
        }

        return removed;
    };

    const postRegistration = (section_id: string) =>
        doAPIRequest("/api/alert/registrations/", "POST", {
            section: section_id,
            auto_resubscribe: true,
            close_notification: email !== "" && closedNotif,
        });

    const submitRegistration = () => {
        // if user has a auto fill section and didn't change the input value then register for section
        // and support user manually entered a course (without checking checkbox)

        if (
            autoCompleteInputRef.current &&
            (autoCompleteInputRef.current.value === autofillSection ||
                (autoCompleteInputRef.current.value !== "" &&
                    selectedCourses.size == 0))
        ) {
            const section = autoCompleteInputRef.current.value;
            isCourseOpen(section).then((isOpen) => {
                postRegistration(section)
                    .then((res) => {
                        if (res.ok) {
                            clearInputValue();
                            setClosedNotif(false);
                        }
                        setResponse(res);
                    })
                    .catch(handleError);
            });
            return;
        }

        // register all selected sections
        const promises: Array<Promise<Response | undefined>> = [];
        selectedCourses.forEach((section) => {
            const promise = isCourseOpen(section.section_id).then((isOpen) => {
                return postRegistration(section.section_id);
            });
            promises.push(promise);
        });

        const sections = Array.from(selectedCourses);

        Promise.allSettled(promises).then((responses) =>
            responses.forEach(
                (res: PromiseSettledResult<Response | undefined>, i) => {
                    //fulfilled if response is returned, even if reg is unsuccessful.
                    if (res.status === "fulfilled") {
                        if (res.value == undefined) {
                            return;
                        }

                        const response: Response = res.value!;

                        setResponse(response);
                        if (response.ok) {
                            deselectCourse(sections[i]);
                            setClosedNotif(false);
                        }
                    } else {
                        //only if network error occurred
                        handleError(res.reason);
                    }
                }
            )
        );
    };

    const onSubmit = () => {
        if (email.length === 0) {
            sendError(
                400,
                "Please enter your email address for alert purposes."
            );
            return;
        }
        if (phone.length !== 0 && !isValidNumber(phone, "US")) {
            sendError(
                400,
                "Please enter a valid phone US # (or leave the field blank)."
            );
            return;
        }

        if (contactInfoChanged()) {
            doAPIRequest("/accounts/me/", "PATCH", {
                profile: { email, phone: parsePhoneNumberFromString(phone, "US")?.number ?? ""},
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
                value={value}
                setValue={setValue}
                setTimeline={setTimeline}
                inputRef={autoCompleteInputRef}
                clearSelections={clearSelections}
                clearInputValue={clearInputValue}
            />
            <Input
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
            />
            <Input
                placeholder="Phone (optional)"
                value={phone}
                onChange={(e) => {
                    setPhone(e.target.value);
                    setPhoneDirty(true);
                }}
            />
            <Center>
                <ClosedText>
                    Notify when closed?&nbsp;
                    <InfoTool text={closeNotifInfoText} />
                    <ClosedCheckbox
                        type="checkbox"
                        checked={closedNotif}
                        onChange={(e) => {
                            setClosedNotif(e.target.checked);
                        }}
                    />
                </ClosedText>

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
