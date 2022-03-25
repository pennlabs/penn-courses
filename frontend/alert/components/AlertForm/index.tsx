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

const Form = styled.form`
    display: flex;
    flex-direction: column;
`;

interface RadioSetProps {
    selected: string;
    options: { label: string; value: string }[];
    setSelected: (val: string) => void;
}

const RadioSet = ({ selected, options, setSelected }: RadioSetProps) => (
    <span>
        {options.map(({ label, value }) => (
            <>
                <label htmlFor={value}>
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
    const [value, setValue] = useState(autofillSection);

    const [email, setEmail] = useState("");

    const [phone, setPhone] = useState("");
    const [isPhoneDirty, setPhoneDirty] = useState(false);

    const [autoResub, setAutoResub] = useState("false");

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

    const isCourseOpen = (section) => {
        return fetch(`/api/base/current/sections/${section}/`).then((res) => 
            res.json().then((courseResult) => {
                const blob = new Blob([JSON.stringify({message: "Course is currently open!", status: 400})], {
                    type: "application/json",
                });

                const isOpen = courseResult["status"] == "O";
                if (isOpen) {
                    setResponse(new Response(blob))
                } 

                return isOpen;
            }))
            .catch((err) => {
                handleError(err);
                return false;
            })
    } 

    const handleError = (e) => {
        console.log(e);
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
    }

    const deselectCourse = (section: Section): boolean => {
        const newSelectedCourses = new Set(selectedCourses);
        const removed = newSelectedCourses.delete(section);
        removed && setSelectedCourses(newSelectedCourses);

        if (newSelectedCourses.size === 0) {
            clearInputValue();
        }

        return removed;
    }

    const submitRegistration = () => {
        // if user has a auto fill section and didn't change the input value then register for section
        // and support user manually entered a course (without checking checkbox)
        if (
            autoCompleteInputRef.current &&
            (autoCompleteInputRef.current.value === autofillSection || (autoCompleteInputRef.current.value !== "" && selectedCourses.size == 0))
        ) {
            isCourseOpen(autoCompleteInputRef.current.value).then(isOpen => {
                if (!isOpen && autoCompleteInputRef.current) {
                    doAPIRequest("/api/alert/registrations/", "POST", {
                        section: autoCompleteInputRef.current.value,
                        auto_resubscribe: autoResub === "true",
                    })
                        .then((res) => {
                            console.log("test")
                            if (res.ok) {
                                clearInputValue();
                            }
                            setResponse(res)
                        })
                        .catch(handleError);
                } 
            })

            return;
            
        }

        // register all selected sections
        const promises: Array<Promise<Response>> = [];
        selectedCourses.forEach((section) => {
            isCourseOpen(section.section_id).then(isOpen => {
                if (!isOpen) {
                    const promise = doAPIRequest("/api/alert/registrations/", "POST", {
                        section: section.section_id,
                        auto_resubscribe: autoResub === "true",
                    });
                    promises.push(promise);
                }
            })
        });

        const sections = Array.from(selectedCourses)

        Promise.allSettled(promises)
            .then((responses) => responses.forEach(
                (res: PromiseSettledResult<Response>, i) => {
                    //fulfilled if response is returned, even if reg is unsuccessful.
                    if (res.status === "fulfilled") {
                        setResponse(res.value);
                        if (res.value.ok) {
                            deselectCourse(sections[i]);
                        } 
                    //only if network error occurred
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
