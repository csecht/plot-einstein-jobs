"""This Module is used only for development. The extract_it() method is
a ad-hoc approach using regex to find tasks of Project sub-series."""
import re
# Copyright (C) 2021 C. Echt under GNU General Public License'


def extract_it(dataframe):
    """
    Use this to extract subprojects. NOT part of plot-einstein-jobs distribution.
    This is only for development.
    """
    # contains() grabs first matches: O2MD1G = O2MD1Gn, O3AS1 = O3AS1a,
    #  so add back the Underscore at end of original sub-proj to make the
    #  where...contains() match unique. From TaskDataFrame.setup_df():
    #    for series in self.gw_series:
    #        is_ser = f'is_{series}'
    #        self.jobs_df[is_ser] = where(
    #        self.jobs_df.task_name.str.contains(series), True, False)

    gw_names_list = dataframe.task_name.where(dataframe.is_fgrp5).to_list()
    pattern = r'__O.+?_'
    matches = [re.search(pattern, name).group() for name in gw_names_list if
               re.search(pattern, name)]
    uniq_matches = sorted(set(matches))
    gw_seriesects = [i.replace('_', '') for i in uniq_matches]
    print('Num of GW sub-projects: ', len(gw_seriesects))
    print('Subprojects: ', gw_seriesects)

    # Num of known GW sub-projects as of 2022 July:  23
    gw_series = ('O2AS20-500', 'O2MD1C1', 'O2MD1C2', 'O2MD1G2', 'O2MD1G_',
                 'O2MD1Gn', 'O2MD1S3', 'O2MDFG2_', 'O2MDFG2e', 'O2MDFG2f',
                 'O2MDFG3_', 'O2MDFG3a', 'O2MDFS2', 'O2MDFS3_', 'O2MDFS3a',
                 'O2MDFV2_', 'O2MDFV2e', 'O2MDFV2g', 'O2MDFV2h', 'O2MDFV2i',
                 'O3AS1_', 'O3AS1a', 'O3ASE1')

    #FGRP5 name structure: LATeah1089F_1128.0_3791580_0.0_0
    grp_names_list = dataframe.task_name.where(
        dataframe.is_gw_O2 & dataframe.is_gw_O3).to_list()
    pattern = r'LATeah.+?_'
    matches = [re.match(pattern, name).group() for name in grp_names_list if
               re.match(pattern, name)]
    uniq_matches = sorted(set(matches))
    grp_subprojects = [i.replace('_', '') for i in uniq_matches]
    print('Num of GR sub-projects: ', len(grp_subprojects))
    print('Subprojects: ', grp_subprojects)
    # Num of GR sub-projects:  360
    #   Five 0000-series categories;
    #   0000F is GRP#5 (Gamma Ray Pulsar Search #5)
    all_gr_subproj = [
        'LATeah0060F', 'LATeah1026F', 'LATeah1028F', 'LATeah1029F', 'LATeah1030F', 'LATeah1031F',
        'LATeah1089F',
        'LATeah1049L05', 'LATeah1049Lba', 'LATeah1049N', 'LATeah1049O', 'LATeah1049P',
        'LATeah1049Q',
        'LATeah1049R', 'LATeah1049S', 'LATeah1049T', 'LATeah1049U', 'LATeah1049V', 'LATeah1049W',
        'LATeah1049X', 'LATeah1049Y', 'LATeah1049ZA', 'LATeah1049ZB', 'LATeah1049ZC',
        'LATeah1049ZD',
        'LATeah1049ZE', 'LATeah1049ZF', 'LATeah1049Z', 'LATeah1049a', 'LATeah1049aa',
        'LATeah1049ab',
        'LATeah1049ac', 'LATeah1049ad', 'LATeah1049ae', 'LATeah1049af', 'LATeah1049ag',
        'LATeah1049b',
        'LATeah1049c',
        'LATeah1061L00', 'LATeah1061L01', 'LATeah1061L02', 'LATeah1061L03', 'LATeah1061L04',
        'LATeah1061L05', 'LATeah1061L06', 'LATeah1061L07', 'LATeah1061L08', 'LATeah1061L09',
        'LATeah1061L10', 'LATeah1061L11', 'LATeah1061L12', 'LATeah1061L13', 'LATeah1061L14',
        'LATeah1061L15', 'LATeah1061L16', 'LATeah1062L00', 'LATeah1062L01', 'LATeah1062L02',
        'LATeah1062L03', 'LATeah1062L04', 'LATeah1062L05', 'LATeah1062L06', 'LATeah1062L07',
        'LATeah1062L08', 'LATeah1062L09', 'LATeah1062L10', 'LATeah1062L11', 'LATeah1062L12',
        'LATeah1062L13', 'LATeah1062L14', 'LATeah1062L15', 'LATeah1062L16', 'LATeah1062L17',
        'LATeah1062L18', 'LATeah1062L19', 'LATeah1062L20', 'LATeah1062L21', 'LATeah1062L22',
        'LATeah1062L23', 'LATeah1062L24', 'LATeah1062L25', 'LATeah1062L26', 'LATeah1062L27',
        'LATeah1062L28', 'LATeah1062L29', 'LATeah1062L30', 'LATeah1062L31', 'LATeah1062L32',
        'LATeah1062L33', 'LATeah1062L34', 'LATeah1062L35', 'LATeah1062L36', 'LATeah1062L37',
        'LATeah1062L38', 'LATeah1062L39', 'LATeah1062L40', 'LATeah1062L41', 'LATeah1063L00',
        'LATeah1063L01',
        'LATeah1063L02', 'LATeah1063L03', 'LATeah1063L04', 'LATeah1063L05', 'LATeah1063L06',
        'LATeah1063L07', 'LATeah1063L08', 'LATeah1063L09', 'LATeah1063L10', 'LATeah1063L11',
        'LATeah1063L12', 'LATeah1063L13', 'LATeah1063L14', 'LATeah1063L15', 'LATeah1063L16',
        'LATeah1063L17', 'LATeah1063L18', 'LATeah1063L19', 'LATeah1063L20', 'LATeah1063L21',
        'LATeah1063L22', 'LATeah1063L23', 'LATeah1063L26', 'LATeah1063L29', 'LATeah1063L30',
        'LATeah1063L31', 'LATeah1063L32', 'LATeah1063L33', 'LATeah1063L37', 'LATeah1063L38',
        'LATeah1063L39', 'LATeah1063L40', 'LATeah1063L41', 'LATeah1063L42', 'LATeah1063L43',
        'LATeah1063L44', 'LATeah1063L45', 'LATeah1063L46', 'LATeah1063L47', 'LATeah1063L48',
        'LATeah1063L49', 'LATeah1063L50', 'LATeah1063L51', 'LATeah1063L52', 'LATeah1063L53',
        'LATeah1064L00', 'LATeah1064L01', 'LATeah1064L02', 'LATeah1064L03', 'LATeah1064L04',
        'LATeah1064L05', 'LATeah1064L06', 'LATeah1064L07', 'LATeah1064L08', 'LATeah1064L09',
        'LATeah1064L10', 'LATeah1064L11', 'LATeah1064L12', 'LATeah1064L13', 'LATeah1064L14',
        'LATeah1064L15', 'LATeah1064L16', 'LATeah1064L17', 'LATeah1064L18', 'LATeah1064L19',
        'LATeah1064L20', 'LATeah1064L22', 'LATeah1064L23', 'LATeah1064L24', 'LATeah1064L25',
        'LATeah1064L26', 'LATeah1064L27', 'LATeah1064L28', 'LATeah1064L29',
        'LATeah1064L31', 'LATeah1064L32', 'LATeah1064L33', 'LATeah1064L34', 'LATeah1064L37',
        'LATeah1064L38', 'LATeah1064L39', 'LATeah1064L40', 'LATeah1064L41', 'LATeah1064L42',
        'LATeah1064L43', 'LATeah1064L44', 'LATeah1064L45', 'LATeah1064L46', 'LATeah1064L47',
        'LATeah1064L48', 'LATeah1064L49', 'LATeah1064L50', 'LATeah1064L51', 'LATeah1064L52',
        'LATeah1064L53', 'LATeah1064L54', 'LATeah1064L55', 'LATeah1064L56', 'LATeah1064L57',
        'LATeah1064L58', 'LATeah1064L59', 'LATeah1064L60', 'LATeah1064L61', 'LATeah1064L62',
        'LATeah1065L00', 'LATeah1065L01', 'LATeah1065L02', 'LATeah1065L03', 'LATeah1065L04',
        'LATeah1065L05', 'LATeah1065L06', 'LATeah1065L07', 'LATeah1065L08', 'LATeah1065L09',
        'LATeah1065L10', 'LATeah1065L11', 'LATeah1065L12', 'LATeah1065L13', 'LATeah1065L14',
        'LATeah1065L15', 'LATeah1065L16', 'LATeah1065L17', 'LATeah1065L18', 'LATeah1065L19',
        'LATeah1065L20', 'LATeah1065L21', 'LATeah1065L22', 'LATeah1065L23', 'LATeah1065L24',
        'LATeah1065L25', 'LATeah1065L26', 'LATeah1065L27', 'LATeah1065L30', 'LATeah1066L03',
        'LATeah1066L05', 'LATeah1066L12', 'LATeah1066L15', 'LATeah1066L16', 'LATeah1066L17',
        'LATeah1066L18', 'LATeah1066L19', 'LATeah1066L20', 'LATeah1066L21', 'LATeah1066L22',
        'LATeah1066L23', 'LATeah1066L24', 'LATeah1066L25', 'LATeah1066L26',
        'LATeah1066L27', 'LATeah1066L28', 'LATeah1066L29', 'LATeah1066L30', 'LATeah1066L31',
        'LATeah1066L32', 'LATeah1066L33', 'LATeah1066L34', 'LATeah1066L35', 'LATeah1066L36',
        'LATeah1066L37', 'LATeah1066L38', 'LATeah1066L39', 'LATeah1066L40', 'LATeah1066L41',
        'LATeah1066L42', 'LATeah1066L43', 'LATeah1066L44', 'LATeah1066L45', 'LATeah1066L46',
        'LATeah1066L47', 'LATeah1066L48', 'LATeah1066L49', 'LATeah1066L50', 'LATeah1066L51',
        'LATeah1066L52', 'LATeah1066L53', 'LATeah1066L54', 'LATeah1066L55', 'LATeah1066L56',
        'LATeah1066L57', 'LATeah1066L58', 'LATeah1066L59', 'LATeah1066L61', 'LATeah1066L62',
        'LATeah1066L63', 'LATeah1066L64', 'LATeah1066L65', 'LATeah1066L66', 'LATeah1066L67',
        'LATeah1066L68', 'LATeah1066L69', 'LATeah1066L70', 'LATeah1066L71', 'LATeah1066L72',
        'LATeah1066L73', 'LATeah1066L74', 'LATeah1066L75', 'LATeah1066L76', 'LATeah1066L77',
        'LATeah1066L78', 'LATeah1066L79', 'LATeah1066L80',
        'LATeah2049Lae', 'LATeah2049Laf', 'LATeah2049Lag', 'LATeah2065L68aj', 'LATeah2065L68ak',
        'LATeah2065L68al', 'LATeah2065L68am', 'LATeah2065L68an',
        'LATeah3001L00', 'LATeah3001L01', 'LATeah3002L00', 'LATeah3002L01', 'LATeah3002L02',
        'LATeah3002L03', 'LATeah3003L00', 'LATeah3003L01', 'LATeah3003L02', 'LATeah3004L01',
        'LATeah3004L02', 'LATeah3004L03', 'LATeah3004L04', 'LATeah3004L05', 'LATeah3011L00',
        'LATeah3011L01', 'LATeah3011L02', 'LATeah3011L03', 'LATeah3011L04', 'LATeah3011L05',
        'LATeah3011L06', 'LATeah3011L07', 'LATeah3011L08', 'LATeah3011L09', 'LATeah3012L00',
        'LATeah3012L01', 'LATeah3012L02', 'LATeah3012L03', 'LATeah3012L04', 'LATeah3012L05',
        'LATeah3012L06', 'LATeah3012L07', 'LATeah3012L08', 'LATeah3012L09', 'LATeah3012L10',
        'LATeah3012L11',
        'LATeah4001L00', 'LATeah4011L00', 'LATeah4011L01', 'LATeah4011L02', 'LATeah4011L03',
        'LATeah4011L04', 'LATeah4012L00', 'LATeah4012L01', 'LATeah4012L02', 'LATeah4012L03',
        'LATeah4012L04', 'LATeah4013L00', 'LATeah4013L01', 'LATeah4013L02', 'LATeah4013L03',
        'LATeah4013L04'
    ]
