import React, { useState } from "react";
import RecBanner from "./RecBanner";
import RecContent from "./RecContent";
import styled from "styled-components";

const RecContainer = styled.div`
    margin-top: auto;
    display: flex;
    flex-direction: column;
    padding: 0 0.9375rem;
`;

const Recs = () => {
    const [show, setShow] = useState(true);

    return (
        <RecContainer>
            {console.log(show)}
            <RecBanner show={show} setShow={setShow} />
            <RecContent show={show} />
        </RecContainer>
    );
};

export default Recs;
