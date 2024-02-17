
import styled from '@emotion/styled';
import { DarkGrayIcon } from '../Requirements/QObject';

const DockWrapper = styled.div`
    z-index: 1;
    opacity: 0.6;
    position: fixed;
    width: 100%;
    bottom: 2%;
    display: flex;
    justify-content: center;
`

const DockContainer = styled.div`
    border-radius: 15px;
    background-color: var(--primary-color-dark);
    height: 6vh;
    min-width: 50vw;
    display: flex;
    justify-content: left;
    padding: 30px;
`

interface IDock {
    setSearchClosed: (status: boolean) => void;
    setReqId: (id: number) => void;
}

const Dock = ({setSearchClosed, setReqId}: IDock) => {
    return (
        <DockWrapper>
            <DockContainer>
                <div onClick={() => {setSearchClosed(false); setReqId(-1);}}>
                    <DarkGrayIcon>
                        <i class="fas fa-search fa-lg"/>
                    </DarkGrayIcon>
                </div>
            </DockContainer>
        </DockWrapper>
    )
}

export default Dock;