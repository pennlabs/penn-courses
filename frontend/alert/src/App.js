import React from "react";
import "./App.css";
import styled from "styled-components";
import Logo from "./assets/PCA_logo.svg";

import {maxWidth, minWidth, PHONE} from "./constants"

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

const Flex = styled.div`
  display: flex;
  flex-direction: ${props => props.col ? 'column' : 'row'};
  align-items: ${props => props.align || 'center'};
`;

const Tagline = styled.h3`
    color: #4A4A4A;
    font-weight: normal;
`;
const Header = styled.h1`
  color: #4A4A4A;

  ${maxWidth(PHONE)} {
    font-size: 1.5rem;
  }
`;

const Input = styled.input`
  outline: none;
  border: 1px solid #d6d6d6;
  color: #4A4A4A;
  font-size: 1.4rem;
  padding: 0.5rem 1rem;
  border-radius: 5px;
  margin: 0.6rem;
  :focus {
    box-shadow: 0 0 0 0.125em rgba(50,115,220,.25)
  }
  ::placeholder{
    color: #D0D0D0;
  }

  ${maxWidth(PHONE)} {
    max-width: 320px;
  }

  ${minWidth(PHONE)} {
    width: 320px;
  }
`;

const Center = styled.div`
  text-align: center;
`

const Footer = styled.div`
  color: #999999;
  font-size: 0.8rem;
  text-align: center;
  position: absolute;
  bottom: 15px;
  width: 100%;
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
  width: 5em;
  padding: 0.7em 1em;
  transition: 0.2s all;
  border: none;
  cursor: pointer;
  :hover{
    background-color: #1496ed;
  }
`;

const Toast = styled.div`
  position: absolute;
  right: 10px;
  top: 10px;
  max-width: 300px;
  /* background-color: */
`;

const TopBanner = (
    <Title>
      We&#39;re currently closed for signups. Come back after schedules have been posted!
    </Title>
);

const LogoArea = () => (
  <Flex>
    <img width="70px" height="70px" src={Logo}/>
    <Header>Penn Course Alert</Header>
  </Flex>
)


const NavContainer = styled.nav`
  margin: 20px;
  display: flex;
  flex-align: left;
  width: 95%;
`;

const NavElt = styled.a`
  padding: 20px;
  color: #4a4a4a;
  font-weight: ${props => props.href === ("/" + window.location.href.split("/")[window.location.href.split("/").length - 1]) ? "bold" : "normal"}
  `

const AlertText = styled.div`
  padding-top: 1rem;
  color: #555555;
`
const Dropdown = styled.span`
  color: #4a4a4a;
  cursor: pointer;
  font-weight: bold;
`;

const Nav = () => (
  <NavContainer>
    <NavElt href="/">Home</NavElt>
    <NavElt href="/manage">Manage Alerts</NavElt>
  </NavContainer>
)

const Heading = () => (
  <Center>
    <LogoArea />
    <Tagline>Get alerted when a course opens up.</Tagline>
  </Center>
)

const AlertForm = ({ onSubmit }) => (
  <>
    <Input autocomplete="off" placeholder="Course"></Input>
    <Input placeholder="Email"></Input>
    <Input placeholder="Phone"></Input>
    <Center>
      <AlertText>Alert me <Dropdown>until I cancel</Dropdown></AlertText>
      <SubmitButton onClick={onSubmit}>Submit</SubmitButton>
    </Center>
  </>
)


function App() {
    const onSubmit = () => { };
    return (
    <Container>
        <Nav />
        <Flex col>
            <Heading />
            <AlertForm onSubmit={onSubmit}/>
        </Flex>
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
