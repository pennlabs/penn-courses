import React from 'react';
import './App.css';
import styled from 'styled-components';
import Logo from './assets/PCA_logo.svg'


const Container = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  height:100vh;
  background: rgb(251, 252, 255);
`

const Title = styled.div`
  width:100%;
  padding: 1.5em 1em;
  background: rgb(235, 76, 100);
  text-align: center;
  color:white;
  font-size: 1rem;
`

const Grid = styled.div`
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-top: 2rem;
`

const Tagline = styled.h3`
    color: #4A4A4A;
    font-weight: normal;
`
const Header = styled.h1`
  color: #4A4A4A
`

const Input = styled.input`
  box-shadow: 0 4px 8px 0 rgba(200, 200, 200, 0.2), 0 6px 20px 0 rgba(200, 200, 200, 0.1);
  outline: none;
  border: none;
  border-radius: 5px;
  color: #4A4A4A;
  font-size: 1.5rem;
  padding: 0.2rem 0.5rem;
  margin: 0.5rem;
  :focused {
    border: 5px solid #3273dc;
  }
  ::placeholder{
    color: #
  }
`

const MiddleArea = styled.div`
  background: rgb(251, 252, 255);
  width: 100%;
`
const TopBanner = (
    <Title>
      We're currently closed for signups. Come back after schedules have been posted!
    </Title>
  );

const LogoArea = (
  <Grid>
    <img width="100px" height="100px" src={require("./assets/PCA_logo.svg")}/>
    <Header>Penn Course Alert</Header>
  </Grid>
)

function App() {
  return (
    <Container>
        {TopBanner}
        {LogoArea}
        <Tagline>Get alerted when a course opens up, by text and email.</Tagline>
        <Input placeholder="Name"></Input>
        <Input placeholder="Email"></Input>
        <Input placeholder="Phone"></Input>
    </Container>
  );
}

export default App;
