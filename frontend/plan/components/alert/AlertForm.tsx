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
    position: fixed;
    height: 200px;
    left: 0;
    top: 0;
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
    setContactInfo: (email: string, phone: string) => void;
    contactInfo: { email: string; phone: string };
    setShowForm: (show: boolean) => void;
}

export default function AlertForm({ setContactInfo, contactInfo, setShowForm }: AlertFormProps) {
    return(
        <Form
            onClick={(e) => e.stopPropagation()}
            onSubmit={(e) => {
                e.preventDefault();
                const email = (e.target as HTMLFormElement).elements[0].value;
                const phone = (e.target as HTMLFormElement).elements[1].value;
                setContactInfo(email, phone);
                setShowForm(false);
            }}
        >
            <Input
                type="email"
                required
                placeholder="Email"
                defaultValue={contactInfo.email}
            />
            <Input
                type="tel"
                placeholder="Phone (optional)"
                defaultValue={contactInfo.phone}
            />
            <SubmitButton type="submit">
                Submit
            </SubmitButton>
        </Form>
    )
}