import dynamic from "next/dynamic";
import Head from "next/head";
import { useRouter } from "next/router";
import styled from "@emotion/styled";
import Select from "react-select";
import useSWR from "swr";
import type { Degree, DegreeListing } from "@/types";

// React Flow and elkjs measure the DOM, so render the graph on the client only.
const DegreeExplorer = dynamic(() => import("@/components/Explorer/DegreeExplorer"), {
  ssr: false,
});

const fetcher = async (url: string) => {
  const res = await fetch(url);
  if (!res.ok) {
    const error = new Error(`Request to ${url} failed with status ${res.status}`) as Error & {
      status: number;
    };
    error.status = res.status;
    throw error;
  }
  return res.json();
};

const Page = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f6f8fa;
`;

const Header = styled.header`
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.6rem 1rem;
  border-bottom: 1px solid #d0d4da;
  background: #fff;
  h1 {
    font-size: 1rem;
    font-weight: 600;
    margin: 0;
    white-space: nowrap;
  }
`;

const Message = styled.div`
  margin: auto;
  color: #57606a;
`;

const degreeLabel = (d: DegreeListing) =>
  [d.year, d.degree, d.major_name || d.major, d.concentration_name || d.concentration]
    .filter(Boolean)
    .join(" · ");

const errorMessage = (error: { status?: number }) =>
  error.status === 401 || error.status === 403
    ? "Log in to Penn Degree Plan (with beta access) to use the explorer."
    : "Couldn't load degrees. Is the backend running?";

/**
 * Internal tool for viewing how a degree's rules fit together. Not linked from the app.
 * The selected degree is kept in the URL (?degree=<id>) so a view can be shared.
 */
export default function ExplorerPage() {
  const router = useRouter();
  const degreeId = typeof router.query.degree === "string" ? router.query.degree : null;

  const { data: degrees, error: listError } = useSWR<DegreeListing[]>(
    "/api/degree/degrees",
    fetcher
  );
  const { data: degree, error: degreeError } = useSWR<Degree>(
    degreeId ? `/api/degree/degrees/${degreeId}` : null,
    fetcher
  );

  const options = (degrees ?? []).map((d) => ({ value: d.id, label: degreeLabel(d) }));
  const error = listError ?? degreeError;

  return (
    <Page>
      <Head>
        <title>Degree Explorer</title>
      </Head>
      <Header>
        <h1>Degree Explorer</h1>
        <div style={{ flex: 1, maxWidth: 560 }}>
          <Select
            instanceId="degree-select"
            placeholder={degrees ? "Pick a degree..." : "Loading degrees..."}
            options={options}
            value={options.find((o) => String(o.value) === degreeId) ?? null}
            onChange={(option) =>
              option && router.push({ query: { degree: option.value } }, undefined, { shallow: true })
            }
          />
        </div>
      </Header>
      {error ? (
        <Message>{errorMessage(error)}</Message>
      ) : !degreeId ? (
        <Message>Pick a degree to see its rule tree.</Message>
      ) : !degree ? (
        <Message>Loading degree...</Message>
      ) : (
        <DegreeExplorer degree={degree} />
      )}
    </Page>
  );
}
