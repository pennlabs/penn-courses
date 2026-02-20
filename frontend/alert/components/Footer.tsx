import React from "react";
import styled from "styled-components";

const Wrapper = styled.div`
    color: #999999;
    font-size: 0.8rem;
    text-align: center;
    bottom: 15px;
    width: 100%;
    padding-top: 3em;
    padding-bottom: 3em;
    line-height: 1.5;
`;

const Footer = () => (
    <Wrapper>
        Made with{" "}
        <span className="icon is-small">
            <i className="fa fa-heart" style={{ color: "red" }} />
        </span>{" "}
        by{" "}
        <a href="http://pennlabs.org" rel="noopener noreferrer" target="_blank">
            Penn Labs
        </a>
        .
        <br />
        Have feedback about Penn Course Alert? Let us know{" "}
        <a href="https://airtable.com/appFRa4NQvNMEbWsA/shrzXeuiEFF8OD89P">here!</a>
    </Wrapper>
);

export default Footer;
