import { useEffect, useState } from "react";
import { FieldValues, useForm } from "react-hook-form";
import { isValidNumber } from "libphonenumber-js";

interface AlertFormModalProps {
    onContactInfoChange?: (email: string, phone: string) => void;
    contactInfo: { email: string; phone: string };
    addAlert?: () => void;
    close: () => void;
}

const AlertFormModal: React.FC<AlertFormModalProps> = ({ onContactInfoChange, contactInfo, addAlert, close }) => {
    const { register, formState: { errors }, handleSubmit } = useForm({defaultValues: contactInfo });

    const submit = (data: FieldValues) => {
        onContactInfoChange?.(data.email, data.phone ?? "");
        addAlert?.();
        close();
    }

    return(
        <form onSubmit={handleSubmit(submit)}>
            <p className="error_message">{errors.email ? "Email cannot be empty." : ""}</p>
            <input {...register("email", { required: true })} placeholder="Email" />
            <p className="error_message">{errors.phone ? "Invalid phone number." : ""}</p>
            <input {...register("phone", { validate: (value, formValues) => !value || isValidNumber(value, "US") })} placeholder="Phone (optional)" />
            <button
                className="button is-link"
                type="submit"
            >
                Submit
            </button>
        </form>
    );
}

export default AlertFormModal;