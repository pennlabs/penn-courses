import React from "react";
import "./App.css";
import styled from "styled-components";
import Logo from "./assets/PCA_logo.svg";


const Container = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  height:100vh;
  background: rgb(251, 252, 255);
`;

const Title = styled.div`
  width:100%;
  padding: 1.5em 1em;
  background: #FF3860;
  text-align: center;
  color:white;
`;

const Grid = styled.div`
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-top: 2rem;
`;

const Tagline = styled.h3`
    color: #4A4A4A;
    font-weight: normal;
`;
const Header = styled.h1`
  color: #4A4A4A
`;

const Input = styled.input`
  box-shadow: 0 4px 8px 0 rgba(200, 200, 200, 0.2), 0 6px 20px 0 rgba(200, 200, 200, 0.1);
  outline: none;
  border: none;
  color: #4A4A4A;
  font-size: 1.4rem;
  padding: 0.5rem 1rem;
  width: 320px;
  margin: 0.6rem;
  :focus {
    box-shadow: 0 0 0 0.125em rgba(50,115,220,.25)
  }
  ::placeholder{
    color: #D0D0D0;
  }
`;

// eslint-disable-next-line
const MiddleArea = styled.div`
  background: rgb(251, 252, 255);
  width: 100%;
`;

const Footer = styled.div`
  color: #999999;
  font-size: 0.8rem;
  text-align: center;
  position: absolute;
  bottom: 15px;
  width: 100%;
  background: white;
  padding-top: 3em;
  padding-bottom:3em;
  line-height:1.5;
`;

const SubmitButton = styled.button`
  border-radius: 5px;
  background-color: #209CEE;
  color: white;
  font-size:1em;
  margin:1em;
  padding: 0.5em 1em;
  transition: 0.2s all;
  border: none;
  cursor: pointer;
  :hover{
    background-color: #1496ed;
  }
`;
const TopBanner = (
    <Title>
      We&#39;re currently closed for signups. Come back after schedules have been posted!
    </Title>
);

const LogoArea = (
    <Grid>
        <img width="100px" height="100px" src={Logo} />
        <Header>Penn Course Alert</Header>
    </Grid>
);


function App() {
    const onSubmit = () => { };
    return (
        <Container>
            {TopBanner}
            {LogoArea}
            <Tagline>Get alerted when a course opens up, by text and email.</Tagline>
            <Input autocomplete="off" placeholder="Course" />
            <Input placeholder="Email" />
            <Input placeholder="Phone" />
            <SubmitButton onClick={onSubmit}>Submit</SubmitButton>
            <Footer>
          Made with
                {" "}
                <span className="icon is-small"><i className="fa fa-heart" style={{ color: "red" }} /></span>
                {" "}
                by
                {" "}
                <a href="http://pennlabs.org" rel="noopener noreferrer" target="_blank">Penn Labs</a>
                {" "}
                .
                <br />
                Have feedback about Penn Course Alert? Let us know
                {" "}
                <a href="https://airtable.com/shra6mktROZJzcDIS">here!</a>
            </Footer>
        </Container>
    );
}

export default App;
