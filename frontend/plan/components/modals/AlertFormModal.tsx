import { isValidNumber } from "libphonenumber-js";
import { useEffect, useState } from "react";

interface AlertFormModalProps {
    onContactInfoChange: (email: string, phone: string) => void;
    contactInfo: { email: string; phone: string };
    addAlert: () => void;
    close: () => void;
}

const AlertFormModal: React.FC<AlertFormModalProps> = ({ onContactInfoChange, contactInfo, addAlert, close }) => {
    const [emailRef, setEmailRef] = useState<HTMLInputElement | null>(null);
    const [phoneRef, setPhoneRef] = useState<HTMLInputElement | null>(null);
    const [email, setEmail] = useState(contactInfo.email);
    const [phone, setPhone] = useState(contactInfo.phone);
    const [emailErrorObj, setEmailErrorObj] = useState({ message: "", error: false });
    const [phoneErrorObj, setPhoneErrorObj] = useState({ message: "", error: false });
    
    useEffect(() => {
        if(email.length === 0) {
            setEmailErrorObj({ message: "Email cannot be empty", error: true });
        } else {
            setEmailErrorObj({ message: "", error: false });
        }

        if(phone && phone.length !== 0 && !isValidNumber(phone, "US")) {
            setPhoneErrorObj({ message: "Invalid phone number", error: true });
        } else {
            setPhoneErrorObj({ message: "", error: false });
        }
    }, [email, phone]);

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
                style={{
                    backgroundColor: emailErrorObj.error ? "#f9dcda" : "#f1f1f1",
                }}
                onChange={() => {
                    setEmail(emailRef?.value || "");
                }}
                placeholder="Email"
            />
            <p className="error_message">{emailErrorObj.message}</p>
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
                disabled={emailErrorObj.error || phoneErrorObj.error}
            >
                Submit
            </button>
        </div>
    )
}

export default AlertFormModal;