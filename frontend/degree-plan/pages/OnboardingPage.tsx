import { Select } from "@radix-ui/themes";
import { Theme } from "@radix-ui/themes";
import { PanelContainer } from "./FourYearPlanPage";
import styled from "@emotion/styled";

const CenteredFlexContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
`;

const ColumnsContainer = styled.div`
  display: flex;
  justify-content: space-between;
  padding-top: 50px;
  padding-left: 100px;
  gap: 20px;

  @media (max-width: 768px) {
    flex-direction: column;
  }
`;

const Column = styled.div`
  flex: 1;
`;

const OnboardingPage = () => {
  // const add_degree = (degreeplanId, degreeId) => {
  //   const updated = postFetcher(
  //     `/api/degree/degreeplans/${degreeplanId}/degrees`,
  //     { degree_ids: [degreeId] }
  //   ); // add degree
  //   mutate(`api/degree/degreeplans/${degreeplanId}`, updated, {
  //     populateCache: true,
  //     revalidate: false,
  //   }); // use updated degree plan returned
  //   mutate(
  //     (key) =>
  //       key &&
  //       key.startsWith(`/api/degree/degreeplans/${degreeplanId}/fulfillments`)
  //   ); // refetch the fulfillments
  // };

  return (
    <Theme>
      <CenteredFlexContainer>
        <PanelContainer $maxWidth="1400px" $minWidth="1400px">
          <h1 style={{ paddingLeft: "100px", paddingTop: "80px" }}>
            Degree Information
          </h1>
          <ColumnsContainer>
            <Column>
              <h5>Starting Year</h5>
              <Select.Root>
                <Select.Trigger placeholder="Select Year Started" />
                <Select.Content>
                  <Select.Item value="2024">2024</Select.Item>
                  <Select.Item value="2023">2023</Select.Item>
                  <Select.Item value="2022">2022</Select.Item>
                  <Select.Item value="2021">2021</Select.Item>
                </Select.Content>
              </Select.Root>

              <h5>Graduation Year</h5>
              <Select.Root>
                <Select.Trigger placeholder="Select Year of Graduation" />
                <Select.Content>
                  <Select.Item value="2024">2024</Select.Item>
                  <Select.Item value="2023">2023</Select.Item>
                  <Select.Item value="2022">2022</Select.Item>
                  <Select.Item value="2021">2021</Select.Item>
                </Select.Content>
              </Select.Root>
            </Column>

            <Column>
              <h5>School or Program</h5>
              <Select.Root>
                <Select.Trigger placeholder="Select School or Program" />
                <Select.Content>
                  <Select.Item value="2024">2024</Select.Item>
                  <Select.Item value="2023">2023</Select.Item>
                  <Select.Item value="2022">2022</Select.Item>
                  <Select.Item value="2021">2021</Select.Item>
                </Select.Content>
              </Select.Root>

              <h5>Major</h5>
              <Select.Root>
                <Select.Trigger placeholder="Major Name, Degree" />
                <Select.Content>
                  <Select.Item value="2024">2024</Select.Item>
                  <Select.Item value="2023">2023</Select.Item>
                  <Select.Item value="2022">2022</Select.Item>
                  <Select.Item value="2021">2021</Select.Item>
                </Select.Content>
              </Select.Root>

              <h5>Minor</h5>
              <Select.Root>
                <Select.Trigger placeholder="Minor Name" />
                <Select.Content>
                  <Select.Item value="2024">2024</Select.Item>
                  <Select.Item value="2023">2023</Select.Item>
                  <Select.Item value="2022">2022</Select.Item>
                  <Select.Item value="2021">2021</Select.Item>
                </Select.Content>
              </Select.Root>
            </Column>
          </ColumnsContainer>
        </PanelContainer>
      </CenteredFlexContainer>
    </Theme>
  );
};

export default OnboardingPage;
