import { useState } from 'react';
import RuleLeaf from './QObject';
import { Fulfillment, Rule as RuleComponent } from '@/types';
import styled from '@emotion/styled';
import { Icon } from '../common/bulma_derived_components';

const RuleTitle = styled.div`
    font-size: 1rem;
    font-weight: 500;
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    background-color: var(--primary-color-light);
    color: #575757;
    padding: 0.25rem .5rem;
    margin: 0.5rem 0;
    border-radius: .5rem;
`

const RuleLeafWrapper = styled.div`
  margin: .5rem;
  margin-left: 0;
  display: flex;
  justify-content: space-between;
  gap: .5rem;
  align-items: center;
`

const CusCourses = styled.div`
  font-weight: 500;
  font-size: .9rem;
  white-space: nowrap;
`

interface RuleProps {
    rule: RuleComponent;
    rulesToFulfillments: { [ruleId: string]: Fulfillment[] };
}

/**
 * Recursive component to represent a rule.
 * @returns 
 */
const RuleComponent = ({ rule, rulesToFulfillments } : RuleProps) => {
    const [collapsed, setCollapsed] = useState(false);
  
    // this is only used when we have a rule leaf
    // TODO: this logic should be moved to the rule leaf
    const fulfillmentsForRule: Fulfillment[] = rulesToFulfillments[rule.id] || [];
    const cus = fulfillmentsForRule.reduce((acc, f) => acc + (f.course?.credits || 1), 0); // default to 1 cu 
    const num = fulfillmentsForRule.length;
    const satisfied = (rule.credits ? cus >= rule.credits : true) && (rule.num ? num >= rule.num : true);

    return (
      <>
        {rule.q ? 
          <RuleLeafWrapper>
              <RuleLeaf q={rule.q} rule={rule} fulfillmentsForRule={fulfillmentsForRule} satisfied={satisfied} />
              {rule.credits && <CusCourses>{cus} / {rule.credits} cus</CusCourses>}
              {" "}
              {rule.num && <CusCourses>{num} / {rule.num}</CusCourses>}
          </RuleLeafWrapper>
          :
          <RuleTitle onClick={() => setCollapsed(!collapsed)}>
            <div>{rule.title}</div>
            {rule.rules.length && 
                <Icon>
                  <i className={`fas fa-chevron-${collapsed ? "up" : "down"}`}></i>
                </Icon>
            }
          </RuleTitle>
          }

        {!collapsed && <div className="ms-3">
            {rule.rules.map((rule: any, index: number) => 
                <RuleComponent key={rule.id} rule={rule} rulesToFulfillments={rulesToFulfillments} />
            )}
          </div>
          }
      </>
    )
}

export default RuleComponent;