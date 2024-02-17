import { GrayIcon } from '@/components/bulma_derived_components';
import styled from '@emotion/styled'

const CloseIcon = styled(GrayIcon)`
  pointer-events: auto;
  margin-left: 0.5rem;

  & :hover {
    color: #707070;
  }
`

const CloseButton = ({ close }) => (
    <CloseIcon onClick={close}>
        <i className="fas fa-times fa-md"></i>
    </CloseIcon>
)

export default CloseButton;