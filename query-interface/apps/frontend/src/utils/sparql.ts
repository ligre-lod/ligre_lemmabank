interface SparqlResponse {
  head: unknown;
  results: {
    distinct: boolean;
    ordered: boolean;
    bindings: SparqlBinding[];
  };
}

interface SparqlBinding {
  [key: string]: {
    type: 'uri' | 'literal';
    value: string;
  };
}

async function client(
  query: string,
  endpointUrl = 'http://localhost:8081/sparql',
): Promise<SparqlResponse> {
   const response = await fetch(endpointUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/sparql-query',
            Accept: 'application/sparql-results+json',
        },
        body:  query ,
    });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const data: SparqlResponse = await response.json();

  return data;
}

function uriToLabel(uri: string, mapping: Record<string, string>): string {
  return mapping[uri] || uri.split('/').pop() || uri;
}

function uriToGenderLabel(uri: string): string {
  return uriToLabel(uri, GENDER_URI_TO_LABEL);
}

function uriToInflectionTypeLabel(uri: string): string {
  return uriToLabel(uri, INFLECTION_TYPE_URI_TO_LABEL);
}

function uriToPosLabel(uri: string): string {
  return uriToLabel(uri, POS_URI_TO_LABEL);
}

const GENDER_URI_TO_LABEL: Record<string, string> = {
  'http://lila-erc.eu/ontologies/lila/feminine': 'Feminine',
  'http://lila-erc.eu/ontologies/lila/masculine': 'Masculine',
  'http://lila-erc.eu/ontologies/lila/neuter': 'Neuter',
};

const INFLECTION_TYPE_URI_TO_LABEL: Record<string, string> = {
  'http://ligre.it/ontologies/ligre/c1': '1st Conjugation',
  'http://ligre.it/ontologies/ligre/c1i': '1st Conj. Irregular',
  'http://ligre.it/ontologies/ligre/c1p': '1st Conj. Procomplementary',
  'http://ligre.it/ontologies/ligre/c1r': '1st Conj. Pronominal',
  'http://ligre.it/ontologies/ligre/c2': '2nd Conjugation',
  'http://ligre.it/ontologies/ligre/c2i': '2nd Conj. Irregular',
  'http://ligre.it/ontologies/ligre/c2p': '2nd Conj. Procomplementary',
  'http://ligre.it/ontologies/ligre/c2r': '2nd Conj. Pronominal',
  'http://ligre.it/ontologies/ligre/c3': '3rd Conjugation',
  'http://ligre.it/ontologies/ligre/c3i': '3rd Conj. Irregular',
  'http://ligre.it/ontologies/ligre/c3p': '3rd Conj. Procomplementary',
  'http://ligre.it/ontologies/ligre/c3r': '3rd Conj. Pronominal',
};

const POS_URI_TO_LABEL: Record<string, string> = {
  'http://lila-erc.eu/ontologies/lila/adjective': 'Adjective',
  'http://lila-erc.eu/ontologies/lila/adposition': 'Adposition',
  'http://lila-erc.eu/ontologies/lila/adverb': 'Adverb',
  'http://lila-erc.eu/ontologies/lila/auxiliary': 'Auxiliary',
  'http://lila-erc.eu/ontologies/lila/coordinating_conjunction':
    'Coordinating Conjunction',
  'http://lila-erc.eu/ontologies/lila/determiner': 'Determiner',
  'http://lila-erc.eu/ontologies/lila/interjection': 'Interjection',
  'http://lila-erc.eu/ontologies/lila/noun': 'Noun',
  'http://lila-erc.eu/ontologies/lila/numeral': 'Numeral',
  'http://lila-erc.eu/ontologies/lila/other': 'Other',
  'http://lila-erc.eu/ontologies/lila/particle': 'Particle',
  'http://lila-erc.eu/ontologies/lila/pronoun': 'Pronoun',
  'http://lila-erc.eu/ontologies/lila/proper_noun': 'Proper Noun',
  'http://lila-erc.eu/ontologies/lila/punctuation': 'Punctuation',
  'http://lila-erc.eu/ontologies/lila/subordinating_conjunction':
    'Subordinating Conjunction',
  'http://lila-erc.eu/ontologies/lila/symbol': 'Symbol',
  'http://lila-erc.eu/ontologies/lila/verb': 'Verb',
};

export interface FilterOption {
  value: string;
  label: string;
}

async function getFilterOptions(predicate: string): Promise<FilterOption[]> {
  const query = `
    SELECT DISTINCT ?object ?label WHERE {
      ?subject <${predicate}> ?object .
      BIND(?object AS ?label)
    } ORDER BY ?label
  `;

  try {
    const data = await client(query);
    return data.results.bindings.map((binding) => {
      const uri = binding.object.value;
      let label: string;

      // Choose the appropriate label mapping based on the predicate
      if (predicate === 'http://lila-erc.eu/ontologies/lila/hasGender') {
        label = uriToGenderLabel(uri);
      } else if (
        predicate === 'http://lila-erc.eu/ontologies/lila/hasInflectionType'
      ) {
        label = uriToInflectionTypeLabel(uri);
      } else if (predicate === 'http://lila-erc.eu/ontologies/lila/hasPOS') {
        label = uriToPosLabel(uri);
      } else {
        // Fallback to the original URI or last part of URI
        label = uri.split('/').pop() || uri;
      }

      return {
        value: uri,
        label: label,
      };
    });
  } catch (error) {
    console.error('Failed to fetch filter options:', error);
    return [];
  }
}

export async function getInflectionOptions(): Promise<FilterOption[]> {
  return getFilterOptions(
    'http://lila-erc.eu/ontologies/lila/hasInflectionType',
  );
}

export async function getPosOptions(): Promise<FilterOption[]> {
  return getFilterOptions('http://lila-erc.eu/ontologies/lila/hasPOS');
}

export async function getGenderOptions(): Promise<FilterOption[]> {
  return getFilterOptions('http://lila-erc.eu/ontologies/lila/hasGender');
}

export interface SearchFilters {
  lemma?: string;
  inflectionType?: string;
  pos?: string;
  gender?: string;
}

export interface SearchResult {
  subject: string;
  wrs: string;
  pos: string;
  lexicons: string;
}

export function generateSparqlQuery(filters: SearchFilters): string {
  const conditions: string[] = [];

  // Add filter conditions based on provided values
  if (filters.gender) {
    conditions.push(
      `?subject <http://lila-erc.eu/ontologies/lila/hasGender> <${filters.gender}> .`,
    );
  }

  if (filters.inflectionType) {
    conditions.push(
      `?subject <http://lila-erc.eu/ontologies/lila/hasInflectionType> <${filters.inflectionType}> .`,
    );
  }

  if (filters.pos) {
    conditions.push(
      `?subject <http://lila-erc.eu/ontologies/lila/hasPOS> <${filters.pos}> .`,
    );
  }

  if (filters.lemma) {
    conditions.push(
      `?subject <http://www.w3.org/ns/lemon/ontolex#writtenRep> ?wrp .`,
    );
    conditions.push(`FILTER regex(?wrp, "${filters.lemma}","i") .`);
  }

  const conditionsString = conditions.join(' ');

  return `
SELECT ?subject ?wrs ?pos ?lexicons where {
  {SELECT ?subject ?poslink ?pos (group_concat(distinct ?wr ; separator=" ") as ?wrs) (group_concat(distinct ?lexicon ; separator=" ") as ?lexicons) WHERE {
      ?subject <http://purl.org/dc/terms/isPartOf> <http://ligre-erc.eu/data/id/lemma/LemmaBank> .
      ${conditionsString}
      ?subject <http://lila-erc.eu/ontologies/lila/hasPOS> ?poslink .
      BIND(?poslink AS ?pos) .
      ?subject <http://www.w3.org/ns/lemon/ontolex#writtenRep> ?wr .
      optional {
          ?le <http://www.w3.org/ns/lemon/ontolex#canonicalForm> ?subject.
          ?lexicon <http://www.w3.org/ns/lemon/lime#entry> ?le .
      }
  } GROUP BY ?subject ?poslink ?pos
  }
} order by ?wrs
  `.trim();
}

export async function searchWithFilters(
  filters: SearchFilters,
): Promise<SearchResult[]> {
  const query = generateSparqlQuery(filters);

  try {
    const data = await client(query);
    return data.results.bindings.map((binding) => ({
      subject: binding.subject.value,
      wrs: binding.wrs.value,
      pos: uriToPosLabel(binding.pos.value),
      lexicons: binding.lexicons.value,
    }));
  } catch (error) {
    console.error('Search query failed:', error);
    return [];
  }
}
