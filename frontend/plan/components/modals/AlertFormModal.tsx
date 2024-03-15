import parsePhoneNumberFromString, { isValidNumber } from "libphonenumber-js";
import { useEffect, useState } from "react";
import styled from "styled-components";

export const Input = styled.input`
    width: auto;
    outline: none;
    border: 1px solid #d6d6d6;
    color: #4a4a4a;
    font-size: 1.4rem;
    padding: 0.5rem 1rem;
    border-radius: 5px;
    margin-bottom: 0.6rem;
    margin-top: 0.6rem;
    :focus {
        box-shadow: 0 0 0 0.125em rgba(50, 115, 220, 0.25);
    }
    ::placeholder {
        color: #d0d0d0;
    }
`;

const Form = styled.form`
    display: flex;
    flex-direction: column;
    height: 200px;
    background-color: white;
    padding: 1em;
`;

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

interface AlertFormProps {
    onContactInfoChange: (email: string, phone: string) => void;
    contactInfo: { email: string; phone: string };
    addAlert: () => void;
    close: () => void;
}

export default function AlertForm({ onContactInfoChange, contactInfo, addAlert, close }: AlertFormProps) {
    const [emailRef, setEmailRef] = useState<HTMLInputElement | null>(null);
    const [phoneRef, setPhoneRef] = useState<HTMLInputElement | null>(null);
    const [email, setEmail] = useState(contactInfo.email);
    const [phone, setPhone] = useState(contactInfo.phone);
    const [phoneErrorObj, setPhoneErrorObj] = useState({ message: "", error: false });

    /*
    useEffect(() => {
        if(phone && phone != "") {
            const parsedNumber = parsePhoneNumberFromString(phone)?.formatNational() || null;
            if(!parsedNumber) {
                setPhoneErrorObj({
                    message: "Invalid phone number",
                    error: true,
                });
            } else {
                setPhone(parsedNumber);
                setPhoneErrorObj({
                    message: "",
                    error: false,
                });
            }
        }
    }, [email, phone]);
    */

    const submit = () => {
        if(!emailRef) {
            return;
        }
        onContactInfoChange(emailRef.value, phoneRef?.value ?? "");
        addAlert();
        close();
    }

    return(
        <div>
            <input
                value={email}
                type="email"
                ref={(ref) => setEmailRef(ref)}
                onChange={() => {
                    setEmail(emailRef?.value || "");
                }}
                placeholder="Email"
            />
            <input
                value={phone}
                type="tel"
                ref={(ref) => setPhoneRef(ref)}
                style={{
                    backgroundColor: phoneErrorObj.error ? "#f9dcda" : "#f1f1f1",
                }}
                onChange={() => {
                    setPhone(phoneRef?.value || "");
                }}
                placeholder="Phone (optional)"
            />
            <p className="error_message">{phoneErrorObj.message}</p>
            <button
                className="button is-link"
                type="button"
                onClick={submit}
            >
                Submit
            </button>
        </div>
    )
}

// export default function AlertForm({ onContactInfoChange, contactInfo, addAlert, close }: AlertFormProps) {
//     return(
//         <Form
//             onClick={(e) => e.stopPropagation()}
//             onSubmit={(e) => {
//                 e.preventDefault();
//                 const email = ((e.target as HTMLFormElement).elements[0] as HTMLInputElement).value;
//                 const phone = ((e.target as HTMLFormElement).elements[1] as HTMLInputElement).value;
//                 onContactInfoChange(email, phone);
//                 addAlert();
//                 close();
//             }}
//         >
//             <Input
//                 type="email"
//                 required
//                 placeholder="Email"
//                 defaultValue={contactInfo.email}
//             />
//             <Input
//                 type="tel"
//                 placeholder="Phone (optional)"
//                 defaultValue={contactInfo.phone}
//             />
//             <SubmitButton type="submit">
//                 Submit
//             </SubmitButton>
//         </Form>
//     )
// }