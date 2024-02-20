import React from 'react';
import Logo from './Logo';
import { type User } from '../../types'
import AccountIndicator from "pcx-shared-components/src/accounts/AccountIndicator";
import { useRouter } from "next/router";
import styled from "@emotion/styled";
import { maxWidth, PHONE } from '../../constants';
import { DarkGrayIcon } from '../Requirements/QObject';

const NavContainer = styled.nav`    
  padding: 0 1rem;
  display: flex;
  flex-align: center;
  width: 100%;
  justify-content: space-between;
  margin: 0 auto;
  background-color: var(--background-grey);
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
              backgroundColor="dark"
              nameLength={2}
              login={login}
              logout={logout}
              />
      </NavElt>
    </NavEltList>
    <NavElt>
      <Logo/>
    </NavElt>
  </NavContainer>
);

export default Nav;