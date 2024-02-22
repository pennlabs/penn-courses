import React from 'react';
import Logo from './Logo';
import { type User } from '../../types'
import AccountIndicator from "pcx-shared-components/src/accounts/AccountIndicator";
import styled from "@emotion/styled";
import Dock from '../Dock/Dock';

const NavContainer = styled.nav`    
  padding: 0 1rem;
  display: flex;
  flex-align: center;
  width: 100%;
  justify-content: space-between;
  margin: 0 auto;
  background-color: #E3E8F4;
`;

const NavElt = styled.span<{ $active?: boolean }>`
  color: #4a4a4a;
  display: flex;
  flex-direction: column;
  justify-content: center;
  font-weight: ${(props) => (props.$active ? "bold" : "normal")};
  cursor: pointer;
  padding-left: 5px;
  padding-right: 5px;
`;

const NavEltList = styled.div`
  display: flex;
  justify-content: left;
`

interface NavProps {
    login: (u: User) => void;
    logout: () => void;
    user: User | null;
}

const Nav = ({ login, logout, user}: NavProps) => (
  <NavContainer>
    <NavEltList>
      <NavElt>
          <AccountIndicator
              leftAligned={true}
              user={user}
              backgroundColor="light"
              nameLength={2}
              login={login}
              logout={logout}
              />
      </NavElt>
    </NavEltList>
    <Dock/>
    <NavElt>
      <Logo/>
    </NavElt>
  </NavContainer>
);

export default Nav;