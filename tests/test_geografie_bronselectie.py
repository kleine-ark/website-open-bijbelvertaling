"""Regressies voor bronweging, Nederlandse labels en legacy-identiteit."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_geografie_buiten_torah as staging
import build_geografie_runtime as runtime


def candidate(modern_id, time, average, lonlat, *, path_score=None, special=None):
    resolution = {'description': '<modern id="m123">Voorbeeld</modern>',
                  'modern_basis_id': modern_id, 'lonlat': lonlat, 'type': 'settlement'}
    if path_score is not None:
        resolution['best_time_score'] = path_score
    if special:
        resolution = {'special': special, 'description': 'not a place'}
    return {'id': modern_id, 'score': {'time_total': time, 'vote_average': average,
                                     'vote_total': 600}, 'resolutions': [resolution]}


def row(*identifications):
    return {'id': 'a21f909', 'url_slug': 'timnah-1', 'friendly_id': 'Timnah 1',
            'identifications': list(identifications)}


class SourceSelectionTests(unittest.TestCase):
    def test_shared_label_for_distinct_entities_requires_review(self):
        mentions = [{'entityId': 'dedan', 'label': 'Dedan', 'status': 'agent-reviewed'},
                    {'entityId': 'rhodes', 'label': 'Dedan', 'status': 'agent-reviewed'},
                    {'entityId': 'other', 'label': 'Andere plaats', 'status': 'agent-reviewed'}]
        self.assertTrue(hasattr(staging, 'review_colliding_mentions'))
        staging.review_colliding_mentions(mentions)
        self.assertEqual([item['status'] for item in mentions],
                         ['needs-human-review', 'needs-human-review', 'agent-reviewed'])

    def test_time_weight_selects_tel_batash_over_rejected_candidate(self):
        result = staging.choose_resolution(row(
            candidate('mc7f587', 836, 22, '34.910297,31.784831'),
            candidate('m0e5df3', -99, 23, '34.935419,31.743041')))
        self.assertEqual(result['lon'], 34.910297)
        self.assertEqual(result['zekerheid'], 'waarschijnlijk')

    def test_intermediate_resolution_confidence_is_included(self):
        result = staging.choose_resolution(row(
            candidate('mweak', 900, 30, '20,30', path_score=100),
            candidate('mbetter', 400, 20, '21,31')))
        self.assertEqual(result['lon'], 21)
        self.assertEqual(result['bron']['score'], 400)

    def test_low_average_does_not_make_consensus_location_uncertain(self):
        result = staging.choose_resolution(row(candidate('mclear', 939, 28, '20,30')))
        self.assertEqual(result['zekerheid'], 'zeker')

    def test_preferred_person_interpretation_is_not_mapped_as_a_city(self):
        self.assertIsNone(staging.choose_resolution(row(
            candidate(None, 993, 27, None, special='not_a_place'),
            candidate('mf10950', -5, 14, '35.124376,31.344952'))))

    def test_nan_coordinates_are_not_published(self):
        self.assertIsNone(staging.choose_resolution(row(candidate('mbad', 1000, 500, 'NaN,30'))))

    def test_source_url_is_specific_and_modern_id_is_resolved(self):
        identification = candidate('mfinal', 750, 20, '20,30')
        identification['id'] = 'aintermediate'
        result = staging.choose_resolution(row(identification))
        self.assertEqual(result['bron']['url'], 'https://www.openbible.info/geo/ancient/a21f909/timnah-1')
        self.assertEqual(result['bron']['modernId'], 'mfinal')
        self.assertEqual(result['bron']['identificationId'], 'aintermediate')
        self.assertEqual(result['bron']['onderbouwing'], 'Voorbeeld')

    def test_alternative_spelling_must_not_steal_another_place_label(self):
        cases = [
            ('ab5175f', 'Ashan', {'Ain': 1, 'Ashan': 39}, 'Ain, Rimmon en Asan.', 'Asan'),
            ('ac24f5f', 'Gibeah 1', {'Geba': 1, 'Gibeah': 404}, 'Geba; Gibeä van Saul vlucht.', 'Gibeä'),
            ('ae981db', 'Mount Seir 1', {'Edom': 1, 'Seir': 237}, 'Seïr en het veld van Edom.', 'Seïr'),
        ]
        for ident, name, labels, text, expected in cases:
            with self.subTest(name=name):
                self.assertEqual(staging.exact_label(text, staging.possible_labels(
                    {'id': ident, 'friendly_id': name, 'translation_name_counts': labels})), expected)

    def test_modern_name_can_come_from_resolved_source_association(self):
        identification = candidate('mfinal', 750, 20, '20,30')
        identification['resolutions'][0]['description'] = 'in the region of the city'
        source = row(identification)
        source['modern_associations'] = {'mfinal': {'name': 'Askar'}}
        self.assertEqual(staging.choose_resolution(source)['bron']['moderneNaam'], 'Askar')


class LegacyIdentityTests(unittest.TestCase):
    def feature(self, ident, name, refs):
        feature = runtime.empty_feature({'id': ident, 'naam': name,
                                         'punt': {'lat': 31, 'lon': 35}})
        for ref in refs:
            runtime.add_ref(feature, runtime.runtime_ref(ref, 'needs-human-review'))
        return feature

    def test_shared_verse_alone_cannot_merge_unrelated_places(self):
        features = {'geo-other': self.feature('geo-other', 'Andere plaats', ['genesis 10:11'])}
        old = {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [43, 36]},
               'properties': {'naam': 'Onbekende stad', 'moderneNaam': 'Verkeerde naam',
                              'verwijzingen': ['genesis 10:11']}}
        with patch.object(runtime, 'read_json', return_value={'features': [old]}):
            runtime.enrich_from_legacy(features)
        self.assertNotEqual('Verkeerde naam', features['geo-other']['properties'].get('moderneNaam'))

    def test_kalach_is_same_entity_as_calah_not_a_second_wrong_point(self):
        features = {'geo-calah-e1f807': self.feature('geo-calah-e1f807', 'Calah',
                                                  ['genesis 10:11', 'genesis 10:12'])}
        old = {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [43.263, 35.46]},
               'properties': {'naam': 'Kalach', 'moderneNaam': 'Nimrud, Irak',
                              'verwijzingen': ['genesis 10:11', 'genesis 10:12']}}
        with patch.object(runtime, 'read_json', return_value={'features': [old]}):
            runtime.enrich_from_legacy(features)
        self.assertEqual(len(features), 1)
        self.assertIn('Kalach', features['geo-calah-e1f807']['properties']['aliases'])
        self.assertIn('geo-legacy-kalach', features['geo-calah-e1f807']['properties'].get('legacyIds', []))


if __name__ == '__main__':
    unittest.main()
