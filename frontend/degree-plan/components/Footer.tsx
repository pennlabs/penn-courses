import styled from "@emotion/styled";

const Wrapper = styled.div`
    color: #999999;
    font-size: 0.8rem;
    text-align: center;
    bottom: 15px;
    width: 100%;
    padding-bottom: 1rem;
    line-height: 1.5;
`;

const Link = styled.a`
    color: rgb(50, 115, 220);
`

const Disclaimer = styled.p`
    color: #777777;
    font-size: 0.7rem;
    margin: 0 auto 0.25rem;
    max-width: 60rem;
    padding: 0 1rem;
`

const Footer = () => (
    <Wrapper>
        <Disclaimer>
            Penn Degree Plan is not an official University of Pennsylvania resource.
            For actual degree planning, please consult your academic advisor.
        </Disclaimer>
        Made with{" "}
        <span className="icon is-small">
            <i className="fa fa-heart" style={{ color: "red" }} />
        </span>{" "}
        by{" "}
        <Link href="http://pennlabs.org" rel="noopener noreferrer" target="_blank">
            Penn Labs
        </Link>
        . 
        Have feedback about Penn Degree Plan? Let us know {" "}
        {// <Link href="mailto:contact@penncourses.org">contact@penncourses.org</Link>
        }
        <Link href="https://airtable.com/appFRa4NQvNMEbWsA/shr120VUScuNJywyv">here!</Link>
    </Wrapper>
);

export default Footer;