import styled from '@emotion/styled';
import { GrayIcon } from './bulma_derived_components';

export const TrashIcon = styled(GrayIcon)`
  pointer-events: auto;
  color: #b2b2b2;
  &:hover {
    color: #7E7E7E;
  }
`;

export const LightTrashIcon = styled(GrayIcon)`
  pointer-events: auto;
  color: #F5F5F5;
  &:hover {
    color: #E0E0E0;
  }
`
